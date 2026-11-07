"""Base entities for Ski Conditions."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, RESORTS
from .coordinator import ResortState, SkiConditionsCoordinator


def hub_device(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_hub")},
        name="Ski Conditions",
        manufacturer=MANUFACTURER,
        model="Data hub",
        entry_type=DeviceEntryType.SERVICE,
    )


class ResortEntity(CoordinatorEntity[SkiConditionsCoordinator]):
    """An entity belonging to one resort device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SkiConditionsCoordinator, resort_id: str, key: str) -> None:
        super().__init__(coordinator)
        self.resort_id = resort_id
        resort = RESORTS[resort_id]
        self._attr_unique_id = f"{resort_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, resort_id)},
            name=resort.name,
            manufacturer=MANUFACTURER,
            model=f"Ski resort ({resort.base_elevation}–{resort.summit_elevation} m)",
            configuration_url=resort.website,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def state_data(self) -> ResortState | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.resort_id)

    @property
    def available(self) -> bool:
        return super().available and self.state_data is not None
