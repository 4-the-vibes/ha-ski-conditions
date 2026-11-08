"""Base entities for Ski Conditions."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .catalog import REGION_NAMES
from .const import DOMAIN, MANUFACTURER, ONTHESNOW_URL, Resort
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

    def __init__(self, coordinator: SkiConditionsCoordinator, resort: Resort, key: str) -> None:
        super().__init__(coordinator)
        self.resort = resort
        self.resort_id = resort.id
        self._attr_unique_id = f"{resort.id}_{key}"
        region = REGION_NAMES.get(resort.region, resort.region)
        url = resort.website or (ONTHESNOW_URL.format(path=resort.onthesnow) if resort.onthesnow else None)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, resort.id)},
            name=resort.name,
            manufacturer=MANUFACTURER,
            model=f"Ski resort{f' · {region}' if region else ''} ({resort.base_elevation}–{resort.summit_elevation} m)",
            configuration_url=url,
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
