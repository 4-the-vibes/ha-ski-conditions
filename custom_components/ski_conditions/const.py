"""Constants for the Ski Conditions integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "ski_conditions"
MANUFACTURER = "Ski Conditions"

CONF_RESORTS = "resorts"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_SOURCES = "sources"  # {resort_id: {"onthesnow": path, "snowforecast": slug}}

DEFAULT_UPDATE_INTERVAL = 30  # minutes
MIN_UPDATE_INTERVAL = 10
MAX_UPDATE_INTERVAL = 1440
STEP_UPDATE_INTERVAL = 5

REQUEST_TIMEOUT = 25  # seconds
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 HomeAssistant-SkiConditions/1.0"
)

ONTHESNOW_URL = "https://www.onthesnow.com/{path}/skireport"
SNOWFORECAST_URL = "https://www.snow-forecast.com/resorts/{slug}/snow-report"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class Resort:
    """Static information about a resort."""

    id: str
    name: str
    latitude: float
    longitude: float
    base_elevation: int  # metres
    summit_elevation: int  # metres
    onthesnow: str  # path segment before /skireport
    snowforecast: str  # snow-forecast.com resort slug
    website: str


RESORTS: dict[str, Resort] = {
    r.id: r
    for r in (
        Resort(
            "sunshine_village",
            "Sunshine Village",
            51.0785,
            -115.7731,
            1660,
            2730,
            "alberta/banff-sunshine",
            "Sunshine",
            "https://www.skibanff.com/conditions",
        ),
        Resort(
            "lake_louise",
            "Lake Louise",
            51.4419,
            -116.1622,
            1646,
            2637,
            "alberta/lake-louise",
            "Lake-Louise",
            "https://www.skilouise.com/snow-conditions/",
        ),
        Resort(
            "panorama",
            "Panorama",
            50.4600,
            -116.2380,
            1150,
            2380,
            "british-columbia/panorama-mountain",
            "Panorama",
            "https://www.panoramaresort.com/conditions/",
        ),
        Resort(
            "kicking_horse",
            "Kicking Horse",
            51.2975,
            -117.0480,
            1190,
            2450,
            "british-columbia/kicking-horse",
            "Kicking-Horse",
            "https://kickinghorseresort.com/conditions/snow-report/",
        ),
        Resort(
            "fernie",
            "Fernie",
            49.4627,
            -115.0873,
            1052,
            2134,
            "british-columbia/fernie-alpine",
            "Fernie",
            "https://skifernie.com/conditions/snow-report/",
        ),
        Resort(
            "castle_mountain",
            "Castle Mountain",
            49.3180,
            -114.4120,
            1425,
            2273,
            "alberta/castle-mountain",
            "Castle-Mountain-Resort",
            "https://www.skicastle.ca/snow-report/",
        ),
    )
}
