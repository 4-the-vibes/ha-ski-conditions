"""Parser tests (run with: pytest tests)."""

import json
from datetime import datetime, timedelta, UTC

from ski_conditions.api import (
    build_open_meteo_params,
    parse_onthesnow,
    parse_open_meteo,
    parse_snowforecast,
    summarize_hours,
)
from ski_conditions.catalog import CATALOG as RESORTS

OTS_META = (
    '<meta name="description" content="The Kicking Horse snow report for Nov 06 is a 4&quot; '
    'base depth with 0 of 5 lifts open.">'
)


def _ots_page(snow: dict | None, extra_text: str = "") -> str:
    nxt = ""
    if snow is not None:
        data = {"props": {"pageProps": {"fullResort": {
            "elevation": {"base": 1190, "top": 2450, "summit": 2450},
            "snow": snow,
            "lifts": {"open": 3, "total": 5},
            "runs": {"open": 40, "total": 130},
            "status": {"openingStatus": "Open"},
        }}}}
        nxt = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'
    return f"<html><head>{OTS_META}</head><body><h1>Kicking Horse</h1>{extra_text}{nxt}</body></html>"


def test_onthesnow_json_metric():
    r = parse_onthesnow(_ots_page({"last24": 15, "last48": 22, "last72": 30, "base": 10, "summit": 85,
                                   "updatedAt": "2026-11-06T07:00:00Z"}))
    assert r.base_depth == 10 and r.summit_depth == 85
    assert (r.snow_24h, r.snow_48h, r.snow_72h) == (15, 22, 30)
    assert (r.lifts_open, r.lifts_total) == (3, 5)
    assert (r.runs_open, r.runs_total) == (40, 130)
    assert r.status == "open"
    assert r.report_date == "2026-11-06T07:00:00Z"


def test_onthesnow_json_inches_calibrated_from_text():
    # text says 4" base; JSON base == 4 -> JSON is inches -> converted
    r = parse_onthesnow(_ots_page({"last24": 2, "base": 4, "summit": 30}))
    assert r.base_depth == 10.2 and r.summit_depth == 76.2 and r.snow_24h == 5.1


def test_onthesnow_text_only():
    r = parse_onthesnow(_ots_page(None, "<div>Lifts Open</div><div>2/5 open</div>"
                                        "<div>Runs Open</div><div>12/130 open</div><span>Packed Powder</span>"))
    assert r.base_depth == 10.2
    assert (r.lifts_open, r.lifts_total) == (0, 5)  # from summary sentence
    assert (r.runs_open, r.runs_total) == (12, 130)
    assert r.surface == "Packed Powder"
    assert r.report_date == "Nov 06"
    assert r.has_data()


def test_onthesnow_garbage():
    r = parse_onthesnow("<html><body>Access denied</body></html>")
    assert not r.has_data()
    assert r.notes


SF_REPORT = """
<html><body>
<h2>Fresh snow depth:</h2><div>No recent snow</div>
<h3>Last significant snowfall:</h3><div><span>Ankle</span> <span>8cm</span> <span>Sun 26 Apr</span> (PM)</div>
<p>Sunshine Village snow depths: updated 29 April 2026</p>
<table>
 <tr><td>Upper snow depth:</td><td></td><td>254 cm</td></tr>
 <tr><td>Lower snow depth:</td><td></td><td>50 cm</td></tr>
</table>
<table><tr><td>Piste conditions:</td><td>Spring snow</td></tr>
<tr><td>Off Piste conditions:</td><td></td></tr>
<tr><td>Lifts open:</td><td>12 out of 12</td></tr></table>
</body></html>
"""

SF_6DAY = """<div>Castle Mountain Resort Snow Conditions</div>
<div>Top snow depth:<b>104cm</b></div><div>Bottom snow depth:<b>104cm</b></div>
<div>Fresh snowfall depth:<b>2cm</b></div><div>Last snowfall:<b>3 Feb 2025</b></div>"""


def test_snowforecast_report_page():
    r = parse_snowforecast(SF_REPORT)
    assert (r.summit_depth, r.base_depth) == (254, 50)
    assert r.fresh_snow == 0
    assert r.last_snowfall_amount == 8 and r.last_snowfall_date == "Sun 26 Apr"
    assert r.report_date == "29 April 2026"
    assert (r.lifts_open, r.lifts_total) == (12, 12)
    assert r.surface == "Spring snow"


def test_snowforecast_6day_layout():
    r = parse_snowforecast(SF_6DAY)
    assert (r.summit_depth, r.base_depth, r.fresh_snow) == (104, 104, 2)
    assert r.last_snowfall_date == "3 Feb 2025"


def _om_location(offset=-25200, start="2026-11-05T00:00", hours=192, snow=0.5):
    t0 = datetime.fromisoformat(start)
    times = [(t0 + timedelta(hours=i)).isoformat(timespec="minutes") for i in range(hours)]
    n = len(times)
    days = [(t0 + timedelta(days=i)).date().isoformat() for i in range(8)]
    return {
        "utc_offset_seconds": offset,
        "current": {"time": "2026-11-06T15:30", "temperature_2m": -6.2, "wind_speed_10m": 22.0,
                    "wind_gusts_10m": 41.0, "wind_direction_10m": 250, "weather_code": 73, "is_day": 1},
        "hourly": {"time": times, "temperature_2m": [-5 - (i % 10) for i in range(n)],
                   "snowfall": [snow] * n, "wind_speed_10m": [10 + i % 30 for i in range(n)],
                   "wind_gusts_10m": [20 + i % 40 for i in range(n)], "precipitation_probability": [50] * n,
                   "freezing_level_height": [1500.0] * n},
        "daily": {"time": days, "snowfall_sum": [3.0] * 8, "temperature_2m_max": [-2] * 8,
                  "temperature_2m_min": [-12] * 8, "weather_code": [73] * 8},
    }


def test_open_meteo_split_and_summary():
    resorts = [RESORTS["fernie"], RESORTS["panorama"]]
    params = build_open_meteo_params(resorts)
    assert params["elevation"] == "2134,1052,2380,1150"
    payload = [_om_location(), _om_location(snow=0.0), _om_location(snow=1.0), _om_location()]
    out = parse_open_meteo(payload, resorts)
    fernie = out["fernie"]
    assert fernie.summit_current["temperature_2m"] == -6.2
    assert fernie.hourly[0]["datetime"].utcoffset() == timedelta(hours=-7)
    now = datetime(2026, 11, 6, 22, 0, tzinfo=UTC)  # 15:00 MST
    nxt = summarize_hours(fernie.hourly, now, now + timedelta(hours=24))
    assert nxt["hours"] == 24 and nxt["snowfall"] == 12.0
    assert nxt["temp_min"] == -14 and nxt["temp_max"] == -5
    assert summarize_hours(out["panorama"].hourly, now, now + timedelta(hours=24))["snowfall"] == 24.0


def test_open_meteo_wrong_count():
    import pytest
    from ski_conditions.api import SourceError
    with pytest.raises(SourceError):
        parse_open_meteo([_om_location()], [RESORTS["fernie"]])


SF_NAKISKA = """<div>The Nakiska snow report is: 0 out of 6 Lifts open.</div>
<div>Ankle</div><div>6 cm</div><div>Wed 28 Oct (PM)</div>
<p>Nakiska snow depths: updated 02 November 2026</p>
<table><tr><td>Upper snow depth:</td><td>0 cm</td></tr><tr><td>Lower snow depth:</td><td>0 cm</td></tr></table>
<table><tr><td>Piste conditions:</td><td>Tell us</td></tr><tr><td>Off Piste conditions:</td><td></td></tr>
<tr><td>Lifts open:</td><td>0 out of 6</td></tr></table>"""


def test_snowforecast_nakiska_preseason():
    r = parse_snowforecast(SF_NAKISKA)
    assert (r.summit_depth, r.base_depth) == (0, 0)
    assert (r.lifts_open, r.lifts_total) == (0, 6)
    assert r.report_date == "02 November 2026"
    assert r.surface is None  # "Tell us" placeholder ignored


def test_all_resorts_in_one_open_meteo_request():
    resorts = [RESORTS[i] for i in ("sunshine_village", "lake_louise", "panorama", "kicking_horse",
                                     "fernie", "castle_mountain", "nakiska", "norquay")]
    params = build_open_meteo_params(resorts)
    assert len(params["elevation"].split(",")) == 16
    out = parse_open_meteo([_om_location() for _ in range(16)], resorts)
    assert set(out) >= {"nakiska", "norquay"}
