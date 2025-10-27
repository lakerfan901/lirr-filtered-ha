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
        _LOGGER.info(
            "Creating sensors for coordinator: station=%s, stop_id=%s, direction_filters=%s, departure_limit=%d",
            coordinator.station_name,
            coordinator.stop_id,
            coordinator.direction_filters,
            coordinator.departure_limit,
        )

        # Create sensors for each direction filter
        for direction_filter in coordinator.direction_filters:
            for idx in range(coordinator.departure_limit):
                sensor = LIRRDepartureSensor(coordinator, entry, direction_filter, idx)
                sensors.append(sensor)
                _LOGGER.debug(
                    "Created sensor: name='%s', unique_id='%s'",
                    sensor.name,
                    sensor.unique_id,
                )

    _LOGGER.info("Total sensors created: %d", len(sensors))
    async_add_entities(sensors, update_before_add=True)


class LIRRDepartureSensor(CoordinatorEntity, SensorEntity):
    """Representation of an LIRR departure sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_suggested_unit_of_measurement = UnitOfTime.MINUTES
    _attr_suggested_display_precision = 0
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LIRRDataUpdateCoordinator,
        entry: ConfigEntry,
        direction_filter: str,
        idx: int
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.direction_filter = direction_filter
        self.idx = idx

        # Use sanitized filter name for entity naming
        # Replace spaces and special characters for cleaner entity IDs
        filter_safe = direction_filter.lower().replace(" ", "_").replace("|", "_")

        self._attr_name = f"{direction_filter} {idx + 1}"
        self._attr_unique_id = f"lirr_{entry.entry_id}_{coordinator.stop_id}_{filter_safe}_{idx}"

    @property
    def native_value(self):
        """Return the state of the sensor in seconds."""
        if not self.coordinator.data:
            return None

        filter_data = self.coordinator.data.get(self.direction_filter, [])
        if len(filter_data) <= self.idx:
            return None

        departure = filter_data[self.idx]
        return departure['minutes_until'] * 60

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        base_attrs = {
            ATTR_STATION: self.coordinator.station_name,
            ATTR_STOP_ID: self.coordinator.stop_id,
            ATTR_DIRECTION_FILTER: self.direction_filter,
            ATTR_ROUTE_FILTER: self.coordinator.route_filter,
        }

        if not self.coordinator.data:
            return base_attrs

        filter_data = self.coordinator.data.get(self.direction_filter, [])
        if len(filter_data) <= self.idx:
            return base_attrs

        departure = filter_data[self.idx]

        return {
            **base_attrs,
            ATTR_HEADSIGN: departure['headsign'],
            ATTR_DEPARTURE_TIME: departure['departure_time'],
            ATTR_MINUTES_UNTIL: departure['minutes_until'],
            ATTR_ROUTE_ID: departure['route_id'],
            ATTR_TRIP_ID: departure['trip_id'],
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
