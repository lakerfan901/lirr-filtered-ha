"""LIRR Data Update Coordinator."""

from datetime import datetime, timedelta
import logging

import aiohttp
from google.transit import gtfs_realtime_pb2

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEPARTURE_LIMIT,
    CONF_DIRECTION_FILTERS,
    CONF_ROUTE_FILTER,
    CONF_STATION_NAME,
    CONF_STOP_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LIRR_GTFS_URL,
    LIRR_STATIC_SCHEDULE_URL,
    STATIC_SCHEDULE_UPDATE_INTERVAL,
)
from .static_schedule import StaticSchedule

_LOGGER = logging.getLogger(__name__)

# Shared static schedule across all coordinators
_SHARED_STATIC_SCHEDULE = None
_SHARED_STATIC_SCHEDULE_LAST_UPDATE = None


async def get_shared_static_schedule(hass: HomeAssistant):
    """Get or create the shared static schedule."""
    global _SHARED_STATIC_SCHEDULE, _SHARED_STATIC_SCHEDULE_LAST_UPDATE

    now = datetime.now()

    if (_SHARED_STATIC_SCHEDULE is None or
        _SHARED_STATIC_SCHEDULE_LAST_UPDATE is None or
        (now - _SHARED_STATIC_SCHEDULE_LAST_UPDATE).total_seconds() > STATIC_SCHEDULE_UPDATE_INTERVAL):

        try:
            _LOGGER.info("Downloading LIRR static schedule (shared)...")
            if _SHARED_STATIC_SCHEDULE is None:
                _SHARED_STATIC_SCHEDULE = StaticSchedule()

            session = async_get_clientsession(hass)
            await _SHARED_STATIC_SCHEDULE.async_load_schedule(LIRR_STATIC_SCHEDULE_URL, session)
            _SHARED_STATIC_SCHEDULE_LAST_UPDATE = now
            _LOGGER.info("Shared static schedule updated successfully")
        except Exception as err:
            _LOGGER.error("Failed to update shared static schedule: %s", err)

    return _SHARED_STATIC_SCHEDULE


class LIRRDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching LIRR data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, station_config: dict) -> None:
        """Initialize."""
        self.stop_id = str(station_config[CONF_STOP_ID])
        self.station_name = station_config[CONF_STATION_NAME]
        self.direction_filters = station_config.get(CONF_DIRECTION_FILTERS, ["All Trains"])
        self.route_filter = station_config.get(CONF_ROUTE_FILTER, "")
        self.departure_limit = int(station_config.get(CONF_DEPARTURE_LIMIT, 8))

        _LOGGER.info(
            "Initialized LIRR coordinator for stop_id: %s, station: %s, direction_filters: %s, route_filter: '%s', departure_limit: %d",
            self.stop_id,
            self.station_name,
            self.direction_filters,
            self.route_filter,
            self.departure_limit,
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.stop_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from LIRR GTFS-RT and organize by direction filter."""
        static_schedule = await get_shared_static_schedule(self.hass)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(LIRR_GTFS_URL, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Error fetching LIRR data: HTTP {response.status}"
                        )

                    data = await response.read()
                    feed = gtfs_realtime_pb2.FeedMessage()
                    feed.ParseFromString(data)

                    _LOGGER.debug("Successfully parsed GTFS-RT feed with %d entities", len(feed.entity))

                    # Collect all departures first
                    all_departures = []
                    current_time = datetime.now()

                    all_stop_ids = set()
                    matched_stops = 0

                    for entity in feed.entity:
                        if not entity.HasField('trip_update'):
                            continue

                        trip_update = entity.trip_update
                        trip = trip_update.trip

                        for stop_time_update in trip_update.stop_time_update:
                            stop_id_str = str(stop_time_update.stop_id)
                            all_stop_ids.add(stop_id_str)

                            if stop_id_str == self.stop_id:
                                matched_stops += 1

                                headsign = static_schedule.get_trip_headsign(trip.trip_id) if static_schedule else ""

                                if not headsign and hasattr(trip, 'trip_headsign') and trip.trip_headsign:
                                    headsign = trip.trip_headsign

                                if not headsign and static_schedule:
                                    route_name = static_schedule.get_route_name(trip.route_id)
                                    if route_name:
                                        headsign = route_name
                                    else:
                                        headsign = f"Route {trip.route_id}"
                                elif not headsign:
                                    headsign = f"Route {trip.route_id}"

                                # Apply route filter if specified
                                if self.route_filter:
                                    route_filters = [f.strip() for f in self.route_filter.split('|') if f.strip()]
                                    if not any(f in trip.route_id for f in route_filters):
                                        _LOGGER.debug(
                                            "Departure filtered out by route: route_id=%s, filter=%s",
                                            trip.route_id,
                                            self.route_filter
                                        )
                                        continue

                                if stop_time_update.HasField('departure'):
                                    dep_time = datetime.fromtimestamp(stop_time_update.departure.time)
                                elif stop_time_update.HasField('arrival'):
                                    dep_time = datetime.fromtimestamp(stop_time_update.arrival.time)
                                else:
                                    _LOGGER.debug("Stop time update has no departure or arrival time")
                                    continue

                                if dep_time < current_time:
                                    _LOGGER.debug("Departure in the past, skipping")
                                    continue

                                minutes_until = int((dep_time - current_time).total_seconds() / 60)

                                all_departures.append({
                                    'headsign': headsign,
                                    'departure_time': dep_time.strftime('%I:%M %p'),
                                    'minutes_until': minutes_until,
                                    'route_id': trip.route_id,
                                    'trip_id': trip.trip_id,
                                })

                    # Sort all departures by time
                    all_departures.sort(key=lambda x: x['minutes_until'])

                    _LOGGER.info(
                        "LIRR Update: stop_id=%s, found %d total departures before filtering",
                        self.stop_id,
                        len(all_departures),
                    )

                    # Log all unique headsigns for debugging
                    unique_headsigns = sorted(set(d['headsign'] for d in all_departures))
                    _LOGGER.info(
                        "Available headsigns at stop %s: %s",
                        self.stop_id,
                        unique_headsigns,
                    )

                    # Filter departures by each direction filter
                    result = {}

                    for direction_filter in self.direction_filters:
                        if direction_filter == "All Trains":
                            # No filtering, just take the next N departures
                            result[direction_filter] = all_departures[:self.departure_limit]
                            _LOGGER.info(
                                "Filter '%s': Selected %d departures (no filtering)",
                                direction_filter,
                                len(result[direction_filter]),
                            )
                        else:
                            # Filter by headsign
                            filtered = []
                            filters = [f.strip() for f in direction_filter.split('|') if f.strip()]

                            _LOGGER.info(
                                "Applying filter '%s' (looking for: %s)",
                                direction_filter,
                                filters,
                            )

                            for departure in all_departures:
                                headsign = departure['headsign']
                                matched = any(f.lower() in headsign.lower() for f in filters)

                                if matched:
                                    filtered.append(departure)
                                    _LOGGER.debug(
                                        "  ✓ Matched: '%s' at %s (%d min)",
                                        headsign,
                                        departure['departure_time'],
                                        departure['minutes_until'],
                                    )
                                    if len(filtered) >= self.departure_limit:
                                        break
                                else:
                                    _LOGGER.debug(
                                        "  ✗ Skipped: '%s' (doesn't match filter)",
                                        headsign,
                                    )

                            result[direction_filter] = filtered
                            _LOGGER.info(
                                "Filter '%s': Found %d/%d matching departures",
                                direction_filter,
                                len(filtered),
                                self.departure_limit,
                            )

                    _LOGGER.info(
                        "LIRR Update: stop_id=%s, matched %d stops, organized into %d direction filters",
                        self.stop_id,
                        matched_stops,
                        len(result),
                    )

                    for filter_name, departures in result.items():
                        _LOGGER.info(
                            "  Filter '%s': %d departures returned",
                            filter_name,
                            len(departures)
                        )

                    if matched_stops == 0:
                        _LOGGER.warning(
                            "No stops found matching stop_id=%s. Sample stop IDs: %s",
                            self.stop_id,
                            list(sorted(all_stop_ids))[:20]
                        )

                    return result

        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with LIRR API: %s", err)
            raise UpdateFailed(f"Error communicating with LIRR API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Error updating LIRR data: %s", err)
            raise UpdateFailed(f"Error updating LIRR data: {err}") from err
