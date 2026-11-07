"""Data sources for Ski Conditions.

Kept free of Home Assistant imports so the parsers can be unit-tested on their own.

Sources
-------
* Open-Meteo  - current weather + hourly/daily forecast, downscaled to summit and
  base elevation. Free JSON API, no key.
* OnTheSnow   - resort-reported base/summit depth, 24/48/72 h snowfall, lifts.
* Snow-Forecast.com - resort-reported top/bottom depth, fresh snow, last snowfall.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any

from .const import (
    ONTHESNOW_URL,
    OPEN_METEO_URL,
    REQUEST_TIMEOUT,
    SNOWFORECAST_URL,
    USER_AGENT,
    Resort,
)

_LOGGER = logging.getLogger(__name__)

INCH_CM = 2.54


class SourceError(Exception):
    """A data source failed."""


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #
@dataclass
class SnowReport:
    """Resort-reported snow figures (all depths in cm)."""

    source: str
    base_depth: float | None = None
    summit_depth: float | None = None
    mid_depth: float | None = None
    snow_24h: float | None = None
    snow_48h: float | None = None
    snow_72h: float | None = None
    snow_7d: float | None = None
    fresh_snow: float | None = None
    last_snowfall_amount: float | None = None
    last_snowfall_date: str | None = None
    lifts_open: int | None = None
    lifts_total: int | None = None
    runs_open: int | None = None
    runs_total: int | None = None
    surface: str | None = None
    status: str | None = None  # "open" / "closed"
    report_date: str | None = None
    notes: list[str] = field(default_factory=list)

    def has_data(self) -> bool:
        return any(
            v is not None
            for v in (
                self.base_depth,
                self.summit_depth,
                self.snow_24h,
                self.fresh_snow,
                self.lifts_open,
            )
        )


@dataclass
class WeatherData:
    """Open-Meteo data for one resort."""

    utc_offset: int
    summit_current: dict[str, Any]
    base_current: dict[str, Any]
    hourly: list[dict[str, Any]]  # each item: {"datetime": aware dt, ...}
    daily: list[dict[str, Any]]  # each item: {"date": date str, ...}
    base_daily: list[dict[str, Any]]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class _TextExtractor(HTMLParser):
    """Turn HTML into whitespace-separated visible text (scripts/styles dropped)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
        if tag == "meta":
            a = dict(attrs)
            if (a.get("name") or a.get("property") or "").lower() in (
                "description",
                "og:description",
            ) and a.get("content"):
                self._parts.append(f" {a['content']} ")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._parts)).strip()


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001 - malformed HTML; fall back to crude strip
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html)))
    return parser.text()


def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group()) if m else None


def _to_cm(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    unit = (unit or "cm").strip().lower()
    if unit in ('"', "in", "inch", "inches", "″"):
        return round(value * INCH_CM, 1)
    if unit in ("m",):
        return round(value * 100, 1)
    return round(value, 1)


# --------------------------------------------------------------------------- #
# OnTheSnow
# --------------------------------------------------------------------------- #
_OTS_SNOW_KEYS = {"last24", "last48", "last72", "base", "summit", "middle", "top"}


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _find_snow_dict(data: Any) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_score = 1
    for node in _walk(data):
        keys = set(node)
        # Must look like a snowfall record, not e.g. an elevation {base, top} object.
        if not keys & {"last24", "last48", "last72"}:
            continue
        score = len(_OTS_SNOW_KEYS & keys)
        nums = [node.get(k) for k in _OTS_SNOW_KEYS if isinstance(node.get(k), (int, float))]
        if score > best_score and nums and max(nums) < 1500:
            best, best_score = node, score
    return best


def _find_open_total(data: Any, key: str) -> tuple[int | None, int | None]:
    for node in _walk(data):
        sub = node.get(key)
        if isinstance(sub, dict) and "open" in sub and "total" in sub:
            o, t = _num(sub.get("open")), _num(sub.get("total"))
            if o is not None or t is not None:
                return (int(o) if o is not None else None, int(t) if t is not None else None)
    return None, None


def parse_onthesnow(html: str) -> SnowReport:
    """Parse an OnTheSnow skireport page."""
    report = SnowReport(source="OnTheSnow")
    text = html_to_text(html)

    # 1) Text: 'The X snow report for Nov 06 is a 4" base depth with 0 of 5 lifts open.'
    text_base_value: float | None = None
    text_base_unit: str | None = None
    m = re.search(
        r"snow report for ([A-Z][a-z]{2,8}\.? \d{1,2}) is an? ([\d.]+)\s*(\"|″|in|cm)\s*base depth"
        r"(?: with (\d+) of (\d+) lifts open)?",
        text,
    )
    if m:
        report.report_date = m.group(1)
        text_base_value, text_base_unit = float(m.group(2)), m.group(3)
        report.base_depth = _to_cm(text_base_value, text_base_unit)
        if m.group(4) is not None:
            report.lifts_open, report.lifts_total = int(m.group(4)), int(m.group(5))
    else:
        report.notes.append("summary sentence not found")

    m = re.search(r"Last Updated:?\s*([A-Z][a-z]{2,8}\.? \d{1,2})", text)
    if m and not report.report_date:
        report.report_date = m.group(1)
    m = re.search(r"Runs Open\s*(\d+)\s*/\s*(\d+)", text)
    if m:
        report.runs_open, report.runs_total = int(m.group(1)), int(m.group(2))
    if report.lifts_open is None:
        m = re.search(r"Lifts Open\s*(\d+)\s*/\s*(\d+)", text)
        if m:
            report.lifts_open, report.lifts_total = int(m.group(1)), int(m.group(2))
    for surface in (
        "Packed Powder",
        "Machine Groomed",
        "Powder",
        "Hard Packed",
        "Spring Snow",
        "Wet Packed",
        "Variable Conditions",
        "Frozen Granular",
        "Loose Granular",
        "Wind Blown",
        "Corn Snow",
        "Icy",
    ):
        if re.search(rf"\b{surface}\b", text):
            report.surface = surface
            break
    m = re.search(r"\b(Open|Closed)\b\s*Recent Snowfall", text)
    if m:
        report.status = m.group(1).lower()

    # 2) Embedded Next.js JSON - more fields, unit-calibrated against the text.
    m = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    if not m:
        report.notes.append("__NEXT_DATA__ not found")
        return report
    try:
        data = json.loads(m.group(1))
    except ValueError:
        report.notes.append("__NEXT_DATA__ not JSON")
        return report

    snow = _find_snow_dict(data)
    if snow:
        factor = 1.0  # assume cm (OnTheSnow stores metric internally)
        j_base = _num(snow.get("base"))
        if j_base and text_base_value:
            text_cm = _to_cm(text_base_value, text_base_unit) or 0
            if abs(j_base - text_base_value) < abs(j_base - text_cm) and text_base_unit != "cm":
                factor = INCH_CM  # JSON is in inches
        def g(*keys: str) -> float | None:
            for k in keys:
                v = _num(snow.get(k))
                if v is not None:
                    return round(v * factor, 1)
            return None

        report.base_depth = g("base") if g("base") is not None else report.base_depth
        report.summit_depth = g("summit", "top", "upper")
        report.mid_depth = g("middle", "mid")
        report.snow_24h = g("last24")
        report.snow_48h = g("last48")
        report.snow_72h = g("last72")
        report.snow_7d = g("last7days", "last168", "weekly")
        for k in ("updatedAt", "updated", "lastUpdated", "date"):
            if isinstance(snow.get(k), str):
                report.report_date = snow[k]
                break
        cond = snow.get("conditions") or snow.get("surface") or snow.get("condition")
        if isinstance(cond, str) and cond:
            report.surface = cond
    else:
        report.notes.append("snow object not found in JSON")

    lo, lt = _find_open_total(data, "lifts")
    if lo is not None:
        report.lifts_open, report.lifts_total = lo, lt
    ro, rt = _find_open_total(data, "runs")
    if ro is not None:
        report.runs_open, report.runs_total = ro, rt
    for node in _walk(data):
        st = node.get("openingStatus") or node.get("status")
        if isinstance(st, str) and st.lower() in ("open", "closed", "temporarily_closed"):
            report.status = "open" if st.lower() == "open" else "closed"
            break
    return report


# --------------------------------------------------------------------------- #
# Snow-Forecast.com
# --------------------------------------------------------------------------- #
_SF_DEPTH = r"([\d.]+)\s*(cm|m|in|\")"


def parse_snowforecast(html: str) -> SnowReport:
    """Parse a snow-forecast.com resort snow-report (or 6day) page."""
    report = SnowReport(source="Snow-Forecast")
    text = html_to_text(html)

    def depth(labels: str) -> float | None:
        m = re.search(rf"(?:{labels}) snow depth:?\s*(?:\|\s*)*{_SF_DEPTH}", text, re.I)
        return _to_cm(float(m.group(1)), m.group(2)) if m else None

    report.summit_depth = depth("Upper|Top")
    report.base_depth = depth("Lower|Bottom")

    m = re.search(
        rf"Fresh snow(?:fall)? depth:?\s*(?:\|\s*)*(?:{_SF_DEPTH}|(No recent snow|-|None))",
        text,
        re.I,
    )
    if m:
        report.fresh_snow = _to_cm(float(m.group(1)), m.group(2)) if m.group(1) else 0.0

    m = re.search(
        rf"Last (?:significant )?snowfall:?\s*(?:[A-Za-z]+\s+)?{_SF_DEPTH}\s*"
        r"((?:[A-Z][a-z]{2} )?\d{1,2} [A-Z][a-z]{2}(?: \d{4})?)",
        text,
    )
    if m:
        report.last_snowfall_amount = _to_cm(float(m.group(1)), m.group(2))
        report.last_snowfall_date = m.group(3)
    else:
        m = re.search(r"Last snowfall:?\s*(\d{1,2} [A-Z][a-z]{2} \d{4})", text)
        if m:
            report.last_snowfall_date = m.group(1)

    m = re.search(r"snow depths:?\s*updated\s*(\d{1,2} [A-Z][a-z]+ \d{4})", text, re.I)
    if m:
        report.report_date = m.group(1)
    m = re.search(r"Lifts open:?\s*(\d+)\s*(?:out of|of|/)\s*(\d+)", text, re.I)
    if m:
        report.lifts_open, report.lifts_total = int(m.group(1)), int(m.group(2))
    m = re.search(r"Piste conditions:?\s*([A-Za-z][A-Za-z ]{2,30}?)\s+(?:Off ?Piste|Next|Lifts)", text)
    if m:
        report.surface = m.group(1).strip()
    if report.summit_depth is None and report.base_depth is None:
        report.notes.append("snow depth labels not found")
    return report


# --------------------------------------------------------------------------- #
# Open-Meteo
# --------------------------------------------------------------------------- #
CURRENT_VARS = (
    "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,"
    "wind_speed_10m,wind_gusts_10m,wind_direction_10m,is_day,cloud_cover,snowfall"
)
HOURLY_VARS = (
    "temperature_2m,apparent_temperature,precipitation_probability,precipitation,"
    "snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,"
    "freezing_level_height,relative_humidity_2m,cloud_cover,is_day"
)
DAILY_VARS = (
    "weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum,"
    "precipitation_sum,precipitation_probability_max,wind_speed_10m_max,"
    "wind_gusts_10m_max,wind_direction_10m_dominant"
)


def build_open_meteo_params(resorts: list[Resort]) -> dict[str, str]:
    """Two points per resort (summit, base) in one request."""
    lats, lons, elevs = [], [], []
    for r in resorts:
        for elev in (r.summit_elevation, r.base_elevation):
            lats.append(f"{r.latitude}")
            lons.append(f"{r.longitude}")
            elevs.append(f"{elev}")
    return {
        "latitude": ",".join(lats),
        "longitude": ",".join(lons),
        "elevation": ",".join(elevs),
        "current": CURRENT_VARS,
        "hourly": HOURLY_VARS,
        "daily": DAILY_VARS,
        "timezone": "auto",
        "past_days": "1",
        "forecast_days": "7",
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }


def _columns_to_rows(block: dict[str, Any]) -> list[dict[str, Any]]:
    times = block.get("time") or []
    keys = [k for k in block if k != "time"]
    return [{"time": t, **{k: (block[k][i] if i < len(block[k]) else None) for k in keys}} for i, t in enumerate(times)]


def parse_open_meteo(payload: Any, resorts: list[Resort]) -> dict[str, WeatherData]:
    """Split an Open-Meteo multi-location response into per-resort data."""
    locations = payload if isinstance(payload, list) else [payload]
    if len(locations) != 2 * len(resorts):
        raise SourceError(
            f"Open-Meteo returned {len(locations)} locations, expected {2 * len(resorts)}"
        )
    out: dict[str, WeatherData] = {}
    for idx, resort in enumerate(resorts):
        summit, base = locations[2 * idx], locations[2 * idx + 1]
        offset = int(summit.get("utc_offset_seconds") or 0)
        tz = timezone(timedelta(seconds=offset))
        hourly = _columns_to_rows(summit.get("hourly") or {})
        for row in hourly:
            row["datetime"] = datetime.fromisoformat(row["time"]).replace(tzinfo=tz)
        out[resort.id] = WeatherData(
            utc_offset=offset,
            summit_current=summit.get("current") or {},
            base_current=base.get("current") or {},
            hourly=hourly,
            daily=_columns_to_rows(summit.get("daily") or {}),
            base_daily=_columns_to_rows(base.get("daily") or {}),
        )
    return out


def summarize_hours(
    hourly: list[dict[str, Any]], start: datetime, end: datetime
) -> dict[str, float | None]:
    """Aggregate hourly rows with start <= t < end."""
    rows = [h for h in hourly if start <= h["datetime"] < end]

    def vals(key: str) -> list[float]:
        return [h[key] for h in rows if isinstance(h.get(key), (int, float))]

    def agg(key: str, fn) -> float | None:
        v = vals(key)
        return round(fn(v), 1) if v else None

    return {
        "hours": len(rows),
        "snowfall": agg("snowfall", sum),
        "precipitation": agg("precipitation", sum),
        "temp_max": agg("temperature_2m", max),
        "temp_min": agg("temperature_2m", min),
        "wind_max": agg("wind_speed_10m", max),
        "gust_max": agg("wind_gusts_10m", max),
        "precip_prob_max": agg("precipitation_probability", max),
        "freezing_level_max": agg("freezing_level_height", max),
        "freezing_level_min": agg("freezing_level_height", min),
    }


# --------------------------------------------------------------------------- #
# Fetching (session is an aiohttp.ClientSession supplied by Home Assistant)
# --------------------------------------------------------------------------- #
async def _get(session: Any, url: str, *, params: dict | None = None, json_: bool = False):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json" if json_ else "text/html,application/xhtml+xml",
        "Accept-Language": "en-CA,en;q=0.9",
    }
    try:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise SourceError(f"HTTP {resp.status} from {url}")
                return await resp.json(content_type=None) if json_ else await resp.text()
    except SourceError:
        raise
    except Exception as err:  # noqa: BLE001 - aiohttp/timeout errors
        raise SourceError(f"{type(err).__name__} fetching {url}: {err}") from err


async def fetch_open_meteo(session: Any, resorts: list[Resort]) -> dict[str, WeatherData]:
    payload = await _get(
        session, OPEN_METEO_URL, params=build_open_meteo_params(resorts), json_=True
    )
    if isinstance(payload, dict) and payload.get("error"):
        raise SourceError(f"Open-Meteo: {payload.get('reason')}")
    return parse_open_meteo(payload, resorts)


async def fetch_onthesnow(session: Any, path: str) -> SnowReport:
    html = await _get(session, ONTHESNOW_URL.format(path=path.strip("/")))
    return parse_onthesnow(html)


async def fetch_snowforecast(session: Any, slug: str) -> SnowReport:
    html = await _get(session, SNOWFORECAST_URL.format(slug=slug.strip("/")))
    return parse_snowforecast(html)
