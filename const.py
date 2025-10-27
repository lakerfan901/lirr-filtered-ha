"""Constants for the LIRR Filtered integration."""

DOMAIN = "lirr_filtered"

# Configuration
CONF_STATIONS = "stations"
CONF_STOP_ID = "stop_id"
CONF_STATION_NAME = "station_name"
CONF_DIRECTION_FILTER = "direction_filter"
CONF_ROUTE_FILTER = "route_filter"
CONF_DEPARTURE_LIMIT = "departure_limit"

# Defaults
DEFAULT_SCAN_INTERVAL = 60  # seconds
DEFAULT_DEPARTURE_LIMIT = 8
STATIC_SCHEDULE_UPDATE_INTERVAL = 86400  # 24 hours in seconds

# LIRR URLs
LIRR_GTFS_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/lirr%2Fgtfs-lirr"
LIRR_STATIC_SCHEDULE_URL = "https://rrgtfsfeeds.s3.amazonaws.com/google_transit.zip"

# Attribute keys
ATTR_HEADSIGN = "headsign"
ATTR_DEPARTURE_TIME = "departure_time"
ATTR_MINUTES_UNTIL = "minutes_until"
ATTR_ROUTE_ID = "route_id"
ATTR_TRIP_ID = "trip_id"
ATTR_DEPARTURES = "departures"
ATTR_NEXT_DEPARTURE = "next_departure"
ATTR_STATION = "station"
ATTR_STOP_ID = "stop_id"
ATTR_DIRECTION_FILTER = "direction_filter"
ATTR_ROUTE_FILTER = "route_filter"