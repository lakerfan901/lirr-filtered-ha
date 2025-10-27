"""Sensor platform for LIRR Filtered."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DEPARTURE_TIME,
    ATTR_DIRECTION_FILTER,
    ATTR_HEADSIGN,
    ATTR_MINUTES_UNTIL,
    ATTR_ROUTE_FILTER,
    ATTR_ROUTE_ID,
    ATTR_STATION,
    ATTR_STOP_ID,
    ATTR_TRIP_ID,
    DOMAIN,
)
from .coordinator import LIRRDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinators: list[LIRRDataUpdateCoordinator] = entry.runtime_data
    
    sensors = []
    for coordinator in coordinators:
        for idx in range(coordinator.departure_limit):
            sensors.append(LIRRDepartureSensor(coordinator, entry, idx))
    
    async_add_entities(sensors, update_before_add=True)


class LIRRDepartureSensor(CoordinatorEntity, SensorEntity):
    """Representation of an LIRR departure sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: LIRRDataUpdateCoordinator,
        entry: ConfigEntry,
        idx: int
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.idx = idx
        self._attr_name = f"LIRR {coordinator.station_name} Departure {idx + 1}"
        self._attr_unique_id = f"lirr_{entry.entry_id}_{coordinator.stop_id}_{idx}"

    @property
    def native_value(self):
        """Return the state of the sensor in seconds."""
        if not self.coordinator.data or len(self.coordinator.data) <= self.idx:
            return None
        
        departure = self.coordinator.data[self.idx]
        return departure['minutes_until'] * 60

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data or len(self.coordinator.data) <= self.idx:
            return {
                ATTR_STATION: self.coordinator.station_name,
                ATTR_STOP_ID: self.coordinator.stop_id,
                ATTR_DIRECTION_FILTER: self.coordinator.direction_filter,
                ATTR_ROUTE_FILTER: self.coordinator.route_filter,
            }
        
        departure = self.coordinator.data[self.idx]
        
        return {
            ATTR_HEADSIGN: departure['headsign'],
            ATTR_DEPARTURE_TIME: departure['departure_time'],
            ATTR_MINUTES_UNTIL: departure['minutes_until'],
            ATTR_ROUTE_ID: departure['route_id'],
            ATTR_TRIP_ID: departure['trip_id'],
            ATTR_STATION: self.coordinator.station_name,
            ATTR_STOP_ID: self.coordinator.stop_id,
            ATTR_DIRECTION_FILTER: self.coordinator.direction_filter,
            ATTR_ROUTE_FILTER: self.coordinator.route_filter,
        }

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:train"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.entry.entry_id}_{self.coordinator.stop_id}")},
            name=f"LIRR {self.coordinator.station_name}",
            manufacturer="MTA Long Island Rail Road",
            model=self.coordinator.stop_id,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update callback."""
        self.async_write_ha_state()