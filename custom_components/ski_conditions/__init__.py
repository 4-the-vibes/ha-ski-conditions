"""Ski Conditions integration for Home Assistant."""

from __future__ import annotations

import logging
from datetime import timedelta
from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .catalog import CATALOG
from .const import (
    CONF_RESORTS,
    CONF_SOURCES,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    SUBENTRY_RESORT,
)
from .coordinator import SkiConditionsCoordinator, get_interval, resorts_fingerprint

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.WEATHER, Platform.NUMBER, Platform.BUTTON]

type SkiConfigEntry = ConfigEntry[SkiConditionsCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SkiConfigEntry) -> bool:
    if CONF_RESORTS in entry.options:  # resorts picked in the initial setup form
        _add_resort_subentries(hass, entry, entry.options[CONF_RESORTS], {})
        hass.config_entries.async_update_entry(
            entry, options={k: v for k, v in entry.options.items() if k != CONF_RESORTS}
        )
    coordinator = SkiConditionsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_entry_updated(hass: HomeAssistant, entry: SkiConfigEntry) -> None:
    """Resort added/removed/edited -> reload. Interval changed -> apply live."""
    coordinator = entry.runtime_data
    if resorts_fingerprint(entry) != coordinator.fingerprint:
        await hass.config_entries.async_reload(entry.entry_id)
        return
    new_interval = timedelta(minutes=get_interval(entry))
    if coordinator.update_interval != new_interval:
        coordinator.update_interval = new_interval
        await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: SkiConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """v1 (resort list in options) -> v2 (one sub-entry per resort).

    Resort ids, and therefore entity unique ids and entity ids, are unchanged.
    """
    if entry.version > 2:
        return False
    if entry.version == 1:
        opts = entry.options
        _add_resort_subentries(
            hass, entry, opts.get(CONF_RESORTS, entry.data.get(CONF_RESORTS, [])), opts.get(CONF_SOURCES, {})
        )
        hass.config_entries.async_update_entry(
            entry,
            data={},
            options={CONF_UPDATE_INTERVAL: int(opts.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))},
            version=2,
        )
        _LOGGER.info("Migrated Ski Conditions to per-resort entries")
    return True


def _add_resort_subentries(
    hass: HomeAssistant, entry: ConfigEntry, resort_ids: list[str], overrides: dict
) -> None:
    """Create a resort sub-entry for each catalog id not already present."""
    existing = {s.unique_id for s in entry.subentries.values()}
    for rid in resort_ids:
        resort = CATALOG.get(rid)
        if resort is None or rid in existing:
            continue
        data = resort.to_dict()
        for key in ("onthesnow", "snowforecast"):
            if key in overrides.get(rid, {}):
                data[key] = overrides[rid][key].strip()
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(data),
                subentry_type=SUBENTRY_RESORT,
                title=resort.name,
                unique_id=rid,
            ),
        )
        existing.add(rid)
