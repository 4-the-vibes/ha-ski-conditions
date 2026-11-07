"""Ski Conditions integration for Home Assistant."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_SOURCES
from .coordinator import SkiConditionsCoordinator, get_interval, get_resort_ids

PLATFORMS = [Platform.SENSOR, Platform.WEATHER, Platform.NUMBER, Platform.BUTTON]

type SkiConfigEntry = ConfigEntry[SkiConditionsCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SkiConfigEntry) -> bool:
    coordinator = SkiConditionsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: SkiConfigEntry) -> None:
    """Reload when resorts/sources change; interval changes apply live."""
    coordinator = entry.runtime_data
    if (
        get_resort_ids(entry) != coordinator.resort_ids
        or entry.options.get(CONF_SOURCES, {}) != coordinator.sources_snapshot
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        return
    new_interval = timedelta(minutes=get_interval(entry))
    if coordinator.update_interval != new_interval:
        coordinator.update_interval = new_interval
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: SkiConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
