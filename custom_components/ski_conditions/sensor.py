"""Sensors for Ski Conditions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import ResortState
from .entity import ResortEntity

# value_fn returns (value, extra_attributes)
ValueFn = Callable[[ResortState], tuple[Any, dict[str, Any]]]

CM = UnitOfLength.CENTIMETERS
WIND_DIRECTION = getattr(SensorDeviceClass, "WIND_DIRECTION", None)
MEASUREMENT_ANGLE = getattr(SensorStateClass, "MEASUREMENT_ANGLE", None)
CARDINALS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


@dataclass(frozen=True, kw_only=True)
class SkiSensorDescription(SensorEntityDescription):
    value_fn: ValueFn


# ----------------------------------------------------------------------------- helpers
def _reported(*candidates: tuple[str, str]) -> ValueFn:
    def fn(st: ResortState) -> tuple[Any, dict[str, Any]]:
        value, source = st.pick(*candidates)
        if source is None:
            return None, {}
        report = st.onthesnow if source == "OnTheSnow" else st.snowforecast
        return value, {
            "source": source,
            "report_date": getattr(report, "report_date", None),
        }
    return fn


def _snow_24h(st: ResortState) -> tuple[Any, dict[str, Any]]:
    value, source = st.pick(("onthesnow", "snow_24h"))
    if value is not None:
        return value, {"source": source, "report_date": st.onthesnow.report_date,
                       "model_estimate": st.past_24h.get("snowfall")}
    return st.past_24h.get("snowfall"), {"source": "Open-Meteo (model estimate)"}


def _current(key: str, where: str = "summit") -> ValueFn:
    def fn(st: ResortState) -> tuple[Any, dict[str, Any]]:
        if not st.weather:
            return None, {}
        cur = st.weather.summit_current if where == "summit" else st.weather.base_current
        elev = st.resort.summit_elevation if where == "summit" else st.resort.base_elevation
        return cur.get(key), {"elevation_m": elev, "observed": cur.get("time")}
    return fn


def _wind_direction(st: ResortState) -> tuple[Any, dict[str, Any]]:
    if not st.weather:
        return None, {}
    deg = st.weather.summit_current.get("wind_direction_10m")
    card = CARDINALS[int((deg % 360) / 22.5 + 0.5) % 16] if isinstance(deg, (int, float)) else None
    return deg, {"cardinal": card}


def _current_hour(st: ResortState, key: str) -> Any:
    if not st.weather:
        return None
    now = dt_util.utcnow()
    for row in st.weather.hourly:
        if row["datetime"] <= now < row["datetime"] + timedelta(hours=1):
            return row.get(key)
    return None


def _next24(key: str) -> ValueFn:
    def fn(st: ResortState) -> tuple[Any, dict[str, Any]]:
        return st.next_24h.get(key), {"hours_covered": st.next_24h.get("hours")}
    return fn


def _week_snow(st: ResortState) -> tuple[Any, dict[str, Any]]:
    if not st.weather:
        return None, {}
    resort_tz = timezone(timedelta(seconds=st.weather.utc_offset))
    today = dt_util.utcnow().astimezone(resort_tz).date().isoformat()
    days = [d for d in st.weather.daily if d["time"] >= today]
    vals = [d.get("snowfall_sum") or 0 for d in days]
    return (round(sum(vals), 1) if days else None), {
        "by_day": {d["time"]: d.get("snowfall_sum") for d in days}
    }


def _summary(st: ResortState) -> tuple[Any, dict[str, Any]]:
    n = st.next_24h
    if not n or n.get("hours") is None:
        return None, {}
    parts = [f"{n.get('snowfall') or 0:g} cm snow"]
    if n.get("temp_max") is not None:
        parts.append(f"{n['temp_max']:g}/{n['temp_min']:g} °C")
    if n.get("gust_max") is not None:
        parts.append(f"gusts {n['gust_max']:g} km/h")
    hourly = []
    if st.weather:
        now = dt_util.utcnow()
        for h in st.weather.hourly:
            if now - timedelta(hours=1) < h["datetime"] <= now + timedelta(hours=24):
                hourly.append({
                    "time": h["datetime"].isoformat(),
                    "temp": h.get("temperature_2m"),
                    "snow": h.get("snowfall"),
                    "wind": h.get("wind_speed_10m"),
                    "gust": h.get("wind_gusts_10m"),
                    "pop": h.get("precipitation_probability"),
                })
    return ", ".join(parts), {"hourly": hourly}


def _last_snowfall(st: ResortState) -> tuple[Any, dict[str, Any]]:
    sf = st.snowforecast
    if not sf or not (sf.last_snowfall_date or sf.last_snowfall_amount):
        return None, {}
    amt = f"{sf.last_snowfall_amount:g} cm" if sf.last_snowfall_amount is not None else ""
    return (f"{amt} on {sf.last_snowfall_date}".strip() if sf.last_snowfall_date else amt), {
        "amount_cm": sf.last_snowfall_amount,
        "date": sf.last_snowfall_date,
        "source": sf.source,
    }


def _open_total(attr_open: str, attr_total: str) -> ValueFn:
    def fn(st: ResortState) -> tuple[Any, dict[str, Any]]:
        value, source = st.pick(("onthesnow", attr_open), ("snowforecast", attr_open))
        report = st.onthesnow if source == "OnTheSnow" else st.snowforecast
        return value, {"total": getattr(report, attr_total, None), "source": source}
    return fn


def _status(st: ResortState) -> tuple[Any, dict[str, Any]]:
    status, source = st.pick(("onthesnow", "status"), ("snowforecast", "status"))
    if status is None:
        lifts, source = st.pick(("onthesnow", "lifts_open"), ("snowforecast", "lifts_open"))
        if lifts is not None:
            status = "open" if lifts > 0 else "closed"
    return status, {"source": source}


def _data_status(st: ResortState) -> tuple[Any, dict[str, Any]]:
    real_errors = {k: v for k, v in st.errors.items() if v != "disabled"}
    have = [k for k in ("open_meteo", "onthesnow", "snowforecast") if k not in st.errors]
    state = "ok" if not real_errors else ("partial" if have or st.weather else "error")
    attrs: dict[str, Any] = {"errors": real_errors or None}
    for k, ts in st.updated.items():
        attrs[f"{k}_last_success"] = ts.isoformat()
    for key, rep in (("onthesnow", st.onthesnow), ("snowforecast", st.snowforecast)):
        if rep is not None and rep.notes:
            attrs[f"{key}_parse_notes"] = rep.notes
    return state, attrs


def depth(key: str, name: str, fn: ValueFn, icon: str = "mdi:snowflake") -> SkiSensorDescription:
    return SkiSensorDescription(
        key=key, name=name, icon=icon, value_fn=fn,
        device_class=SensorDeviceClass.DISTANCE, native_unit_of_measurement=CM,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0,
    )


def temp(key: str, name: str, fn: ValueFn) -> SkiSensorDescription:
    return SkiSensorDescription(
        key=key, name=name, value_fn=fn,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=1,
    )


def wind(key: str, name: str, fn: ValueFn) -> SkiSensorDescription:
    return SkiSensorDescription(
        key=key, name=name, value_fn=fn,
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0,
    )


SENSORS: tuple[SkiSensorDescription, ...] = (
    # --- resort-reported snow ---------------------------------------------------
    depth("base_depth", "Base depth",
          _reported(("onthesnow", "base_depth"), ("snowforecast", "base_depth")), "mdi:arrow-collapse-down"),
    depth("summit_depth", "Summit depth",
          _reported(("onthesnow", "summit_depth"), ("snowforecast", "summit_depth")), "mdi:image-filter-hdr"),
    depth("powder_depth", "Powder depth",
          _reported(("snowforecast", "fresh_snow"), ("onthesnow", "snow_24h")), "mdi:weather-snowy-heavy"),
    depth("snowfall_24h", "Snowfall 24h", _snow_24h, "mdi:weather-snowy"),
    depth("snowfall_48h", "Snowfall 48h", _reported(("onthesnow", "snow_48h")), "mdi:weather-snowy"),
    depth("snowfall_72h", "Snowfall 72h", _reported(("onthesnow", "snow_72h")), "mdi:weather-snowy"),
    SkiSensorDescription(key="last_snowfall", name="Last snowfall", icon="mdi:calendar-clock",
                         value_fn=_last_snowfall),
    SkiSensorDescription(key="lifts_open", name="Lifts open", icon="mdi:gondola",
                         value_fn=_open_total("lifts_open", "lifts_total"),
                         state_class=SensorStateClass.MEASUREMENT),
    SkiSensorDescription(key="runs_open", name="Runs open", icon="mdi:ski",
                         value_fn=_open_total("runs_open", "runs_total"),
                         state_class=SensorStateClass.MEASUREMENT),
    SkiSensorDescription(key="surface", name="Surface conditions", icon="mdi:snowflake-variant",
                         value_fn=_reported(("onthesnow", "surface"), ("snowforecast", "surface"))),
    SkiSensorDescription(key="status", name="Resort status", icon="mdi:ski-water",
                         value_fn=_status),
    SkiSensorDescription(key="report_date", name="Report date", icon="mdi:calendar",
                         value_fn=_reported(("onthesnow", "report_date"), ("snowforecast", "report_date"))),
    # --- current weather (Open-Meteo) -------------------------------------------
    temp("summit_temperature", "Summit temperature", _current("temperature_2m", "summit")),
    temp("base_temperature", "Base temperature", _current("temperature_2m", "base")),
    temp("summit_feels_like", "Summit feels like", _current("apparent_temperature", "summit")),
    wind("wind_speed", "Summit wind", _current("wind_speed_10m", "summit")),
    wind("wind_gust", "Summit wind gust", _current("wind_gusts_10m", "summit")),
    wind("base_wind_speed", "Base wind", _current("wind_speed_10m", "base")),
    SkiSensorDescription(key="wind_direction", name="Summit wind direction", icon="mdi:compass",
                         value_fn=_wind_direction, native_unit_of_measurement="°",
                         device_class=WIND_DIRECTION, state_class=MEASUREMENT_ANGLE),
    SkiSensorDescription(key="freezing_level", name="Freezing level", icon="mdi:thermometer-lines",
                         value_fn=lambda st: (_current_hour(st, "freezing_level_height"), {}),
                         device_class=SensorDeviceClass.DISTANCE,
                         native_unit_of_measurement=UnitOfLength.METERS,
                         state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0),
    depth("model_snowfall_past_24h", "Snowfall past 24h (model)",
          lambda st: (st.past_24h.get("snowfall"), {"source": "Open-Meteo"}), "mdi:weather-snowy"),
    # --- 24 h forecast ----------------------------------------------------------
    depth("forecast_snowfall_24h", "Forecast snowfall next 24h", _next24("snowfall"), "mdi:weather-snowy-heavy"),
    temp("forecast_high_24h", "Forecast high next 24h", _next24("temp_max")),
    temp("forecast_low_24h", "Forecast low next 24h", _next24("temp_min")),
    wind("forecast_wind_max_24h", "Forecast max wind next 24h", _next24("wind_max")),
    wind("forecast_gust_max_24h", "Forecast max gust next 24h", _next24("gust_max")),
    SkiSensorDescription(key="forecast_precip_probability_24h", name="Forecast precipitation chance next 24h",
                         icon="mdi:umbrella-outline", value_fn=_next24("precip_prob_max"),
                         native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SkiSensorDescription(key="forecast_freezing_level_24h", name="Forecast max freezing level next 24h",
                         icon="mdi:thermometer-lines", value_fn=_next24("freezing_level_max"),
                         device_class=SensorDeviceClass.DISTANCE,
                         native_unit_of_measurement=UnitOfLength.METERS,
                         state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=0),
    SkiSensorDescription(key="forecast_summary_24h", name="Forecast next 24h", icon="mdi:weather-partly-snowy",
                         value_fn=_summary),
    depth("forecast_snowfall_7d", "Forecast snowfall 7 days", _week_snow, "mdi:calendar-week"),
    # --- diagnostics ------------------------------------------------------------
    SkiSensorDescription(key="data_status", name="Data status", icon="mdi:database-check",
                         value_fn=_data_status, entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        SkiSensor(coordinator, rid, desc) for rid in coordinator.resort_ids for desc in SENSORS
    )


class SkiSensor(ResortEntity, SensorEntity):
    entity_description: SkiSensorDescription

    def __init__(self, coordinator, resort_id: str, description: SkiSensorDescription) -> None:
        super().__init__(coordinator, resort_id, description.key)
        self.entity_description = description

    def _value(self) -> tuple[Any, dict[str, Any]]:
        st = self.state_data
        if st is None:
            return None, {}
        try:
            return self.entity_description.value_fn(st)
        except (KeyError, TypeError, ValueError, AttributeError):
            return None, {}

    @property
    def native_value(self) -> Any:
        return self._value()[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = {k: v for k, v in self._value()[1].items() if v is not None}
        return attrs or None
