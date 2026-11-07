"""Update-interval control for Ski Conditions."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MAX_UPDATE_INTERVAL, MIN_UPDATE_INTERVAL, STEP_UPDATE_INTERVAL
from .coordinator import SkiConditionsCoordinator, get_interval
from .entity import hub_device


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([UpdateIntervalNumber(entry.runtime_data)])


class UpdateIntervalNumber(NumberEntity):
    """Minutes between refreshes. Changes apply immediately, no reload."""

    _attr_has_entity_name = True
    _attr_name = "Update interval"
    _attr_icon = "mdi:timer-cog-outline"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = MIN_UPDATE_INTERVAL
    _attr_native_max_value = MAX_UPDATE_INTERVAL
    _attr_native_step = STEP_UPDATE_INTERVAL
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(self, coordinator: SkiConditionsCoordinator) -> None:
        self.coordinator = coordinator
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_update_interval"
        self._attr_device_info = hub_device(entry.entry_id)

    @property
    def native_value(self) -> float:
        return get_interval(self.coordinator.config_entry)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_interval(int(value))
        self.async_write_ha_state()
