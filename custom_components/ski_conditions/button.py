"""Manual refresh button for Ski Conditions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SkiConditionsCoordinator
from .entity import hub_device


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([RefreshButton(entry.runtime_data)])


class RefreshButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Refresh now"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: SkiConditionsCoordinator) -> None:
        self.coordinator = coordinator
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = hub_device(entry.entry_id)

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
