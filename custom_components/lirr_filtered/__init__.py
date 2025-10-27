"""The LIRR Filtered integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEPARTURE_LIMIT,
    CONF_DIRECTION_FILTER,
    CONF_DIRECTION_FILTERS,
    CONF_ROUTE_FILTER,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_STOP_ID,
    DEFAULT_DEPARTURE_LIMIT,
    DOMAIN,
)
from .coordinator import LIRRDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]

type LIRRFilteredConfigEntry = ConfigEntry[list[LIRRDataUpdateCoordinator]]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry format to new format."""
    _LOGGER.info("Migrating LIRR Filtered entry from version %s", entry.version)

    if entry.version == 1:
        old_data = dict(entry.data)

        # Check if already in new format with CONF_STATIONS
        if CONF_STATIONS in old_data:
            # Check if stations need migration from direction_filter to direction_filters
            stations = list(old_data[CONF_STATIONS])
            migrated = False

            for station in stations:
                if CONF_DIRECTION_FILTER in station and CONF_DIRECTION_FILTERS not in station:
                    # Migrate from old direction_filter (string) to new direction_filters (list)
                    direction_filter = station.get(CONF_DIRECTION_FILTER, "")
                    if direction_filter:
                        # Split by | if multiple filters, otherwise use as single filter
                        filters = [f.strip() for f in direction_filter.split('|') if f.strip()]
                        station[CONF_DIRECTION_FILTERS] = filters if filters else ["All Trains"]
                    else:
                        station[CONF_DIRECTION_FILTERS] = ["All Trains"]

                    # Remove old direction_filter key
                    station.pop(CONF_DIRECTION_FILTER, None)
                    migrated = True
                    _LOGGER.info("Migrated station %s from direction_filter to direction_filters", station.get(CONF_STATION_NAME))

            if migrated:
                hass.config_entries.async_update_entry(
                    entry,
                    data={CONF_STATIONS: stations},
                    version=1,
                )
                _LOGGER.info("Migration to direction_filters successful")

            return True

        # Old format: single station config directly in entry.data
        # Migrate to new format with direction_filters
        direction_filter = old_data.get(CONF_DIRECTION_FILTER, "")
        if direction_filter:
            filters = [f.strip() for f in direction_filter.split('|') if f.strip()]
            direction_filters = filters if filters else ["All Trains"]
        else:
            direction_filters = ["All Trains"]

        station_config = {
            CONF_STATION_NAME: old_data.get(CONF_STATION_NAME, "LIRR Station"),
            CONF_STOP_ID: old_data.get(CONF_STOP_ID, ""),
            CONF_DIRECTION_FILTERS: direction_filters,
            CONF_ROUTE_FILTER: old_data.get(CONF_ROUTE_FILTER, ""),
            CONF_DEPARTURE_LIMIT: old_data.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT),
        }

        new_data = {
            CONF_STATIONS: [station_config]
        }

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            version=1,
        )

        _LOGGER.info("Migration from old format successful")
        return True

    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: LIRRFilteredConfigEntry
) -> bool:
    """Set up LIRR Filtered from a config entry."""
    stations = entry.data.get(CONF_STATIONS, [])
    
    # Handle empty stations (shouldn't happen, but just in case)
    if not stations:
        _LOGGER.error("No stations configured in entry")
        return False
    
    coordinators = []
    for station_config in stations:
        coordinator = LIRRDataUpdateCoordinator(hass, entry, station_config)
        await coordinator.async_config_entry_first_refresh()
        coordinators.append(coordinator)
    
    entry.runtime_data = coordinators
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)