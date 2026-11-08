"""Constants for the Ski Conditions integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

DOMAIN = "ski_conditions"
MANUFACTURER = "Ski Conditions"
SUBENTRY_RESORT = "resort"

CONF_RESORTS = "resorts"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_SOURCES = "sources"  # v1 only (migrated into subentries)

DEFAULT_UPDATE_INTERVAL = 30  # minutes
MIN_UPDATE_INTERVAL = 10
MAX_UPDATE_INTERVAL = 1440
STEP_UPDATE_INTERVAL = 5

REQUEST_TIMEOUT = 25  # seconds
OPEN_METEO_MAX_RESORTS_PER_CALL = 25
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36 HomeAssistant-SkiConditions/2.0"
)

ONTHESNOW_URL = "https://www.onthesnow.com/{path}/skireport"
SNOWFORECAST_URL = "https://www.snow-forecast.com/resorts/{slug}/snow-report"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class Resort:
    """Everything the integration needs to know about one resort."""

    id: str
    name: str
    latitude: float
    longitude: float
    base_elevation: int  # metres
    summit_elevation: int  # metres
    onthesnow: str = ""  # path before /skireport; "" disables the source
    snowforecast: str = ""  # snow-forecast.com slug; "" disables the source
    region: str = ""
    country: str = ""
    website: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Resort:
        names = {f.name for f in fields(cls)}
        d = {k: v for k, v in data.items() if k in names}
        d["latitude"] = float(d["latitude"])
        d["longitude"] = float(d["longitude"])
        d["base_elevation"] = int(d["base_elevation"])
        d["summit_elevation"] = int(d["summit_elevation"])
        for k in ("onthesnow", "snowforecast", "region", "country", "website"):
            d[k] = (d.get(k) or "").strip()
        return cls(**d)
