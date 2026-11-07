"""Data update coordinator for Ski Conditions."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    SnowReport,
    SourceError,
    WeatherData,
    fetch_onthesnow,
    fetch_open_meteo,
    fetch_snowforecast,
    summarize_hours,
)
from .const import (
    CONF_RESORTS,
    CONF_SOURCES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    RESORTS,
    Resort,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class ResortState:
    """Everything known about one resort after an update."""

    resort: Resort
    weather: WeatherData | None = None
    onthesnow: SnowReport | None = None
    snowforecast: SnowReport | None = None
    next_24h: dict[str, Any] = field(default_factory=dict)
    past_24h: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    updated: dict[str, datetime] = field(default_factory=dict)

    # ---- merged, reported-first values ---------------------------------- #
    def pick(self, *candidates: tuple[str, str]) -> tuple[Any, str | None]:
        """Return the first non-None (value, source) from (source, attr) pairs."""
        for src, attr in candidates:
            obj = {"onthesnow": self.onthesnow, "snowforecast": self.snowforecast}.get(src)
            if obj is not None and getattr(obj, attr, None) is not None:
                return getattr(obj, attr), obj.source
        return None, None


def get_interval(entry: ConfigEntry) -> int:
    return int(
        entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
    )


def get_resort_ids(entry: ConfigEntry) -> list[str]:
    ids = entry.options.get(CONF_RESORTS, entry.data.get(CONF_RESORTS, list(RESORTS)))
    return [i for i in ids if i in RESORTS]


class SkiConditionsCoordinator(DataUpdateCoordinator[dict[str, ResortState]]):
    """Fetch all sources for all selected resorts."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=get_interval(entry)),
        )
        self.resort_ids = get_resort_ids(entry)
        self.sources_snapshot = dict(entry.options.get(CONF_SOURCES, {}))
        self._session = async_get_clientsession(hass)
        self._sem = asyncio.Semaphore(3)
        self._last: dict[str, ResortState] = {}

    @property
    def resorts(self) -> list[Resort]:
        return [RESORTS[i] for i in self.resort_ids]

    def _source(self, resort: Resort, key: str) -> str:
        overrides = self.config_entry.options.get(CONF_SOURCES, {}).get(resort.id, {})
        return (overrides.get(key) or getattr(resort, key)).strip()

    async def async_set_interval(self, minutes: int) -> None:
        """Change polling interval live (called by the number entity).

        Persisting to options fires the update listener, which applies the new
        interval and triggers a refresh (that also reschedules the timer).
        """
        options = {**self.config_entry.options, CONF_UPDATE_INTERVAL: int(minutes)}
        self.hass.config_entries.async_update_entry(self.config_entry, options=options)

    async def _guarded(self, coro):
        async with self._sem:
            return await coro

    async def _async_update_data(self) -> dict[str, ResortState]:
        resorts = self.resorts
        now = dt_util.utcnow()

        jobs: list[Any] = [fetch_open_meteo(self._session, resorts)]
        for r in resorts:
            path, slug = self._source(r, "onthesnow"), self._source(r, "snowforecast")
            jobs.append(self._guarded(fetch_onthesnow(self._session, path)) if path else _none())
            jobs.append(self._guarded(fetch_snowforecast(self._session, slug)) if slug else _none())
        results = await asyncio.gather(*jobs, return_exceptions=True)

        weather_all = results[0]
        weather_err = None
        if isinstance(weather_all, BaseException):
            weather_err = str(weather_all)
            _LOGGER.warning("Open-Meteo update failed: %s", weather_all)
            weather_all = {}

        states: dict[str, ResortState] = {}
        any_ok = bool(weather_all)
        for i, r in enumerate(resorts):
            prev = self._last.get(r.id) or ResortState(resort=r)
            st = ResortState(resort=r, updated=dict(prev.updated))

            # weather
            if r.id in weather_all:
                st.weather = weather_all[r.id]
                st.updated["open_meteo"] = now
            else:
                st.weather = prev.weather  # keep last good
                st.errors["open_meteo"] = weather_err or "no data"

            # reports
            for key, res in (("onthesnow", results[1 + 2 * i]), ("snowforecast", results[2 + 2 * i])):
                if isinstance(res, SnowReport) and res.has_data():
                    setattr(st, key, res)
                    st.updated[key] = now
                    any_ok = True
                    if res.notes:
                        _LOGGER.debug("%s %s parse notes: %s", r.name, key, res.notes)
                else:
                    setattr(st, key, getattr(prev, key))
                    if isinstance(res, BaseException):
                        st.errors[key] = str(res)
                    elif isinstance(res, SnowReport):
                        st.errors[key] = "page parsed but no values found: " + "; ".join(res.notes)
                    elif res is None:
                        st.errors[key] = "disabled"
                    if key in st.errors and st.errors[key] != "disabled":
                        _LOGGER.debug("%s %s: %s", r.name, key, st.errors[key])

            if st.weather:
                st.next_24h = summarize_hours(st.weather.hourly, now, now + timedelta(hours=24))
                st.past_24h = summarize_hours(st.weather.hourly, now - timedelta(hours=24), now)
            states[r.id] = st

        if not any_ok and not self._last:
            raise UpdateFailed(f"All sources failed. Open-Meteo: {weather_err}")
        self._last = states
        return states


async def _none() -> None:
    return None


__all__ = ["SkiConditionsCoordinator", "ResortState", "SourceError"]
