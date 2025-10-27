"""GTFS Static Schedule Parser for LIRR."""

import csv
import io
import logging
from typing import Dict
import zipfile

import aiohttp

_LOGGER = logging.getLogger(__name__)


class StaticSchedule:
    """Parse and store GTFS static schedule data."""

    def __init__(self):
        """Initialize static schedule."""
        self.trip_headsigns: Dict[str, str] = {}
        self.route_names: Dict[str, str] = {}
        self.stop_names: Dict[str, str] = {}

    async def async_load_schedule(self, url: str, session: aiohttp.ClientSession = None):
        """Download and parse GTFS static schedule."""
        try:
            if session is None:
                async with aiohttp.ClientSession() as new_session:
                    return await self._download_and_parse(url, new_session)
            else:
                return await self._download_and_parse(url, session)
        except Exception as err:
            _LOGGER.error("Error loading static schedule: %s", err)
            raise

    async def _download_and_parse(self, url: str, session: aiohttp.ClientSession):
        """Download and parse the GTFS static zip file."""
        _LOGGER.info("Downloading LIRR static schedule from %s", url)
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                raise Exception(f"Failed to download static schedule: HTTP {response.status}")
            
            zip_data = await response.read()
        
        _LOGGER.info("Downloaded %d bytes, parsing schedule...", len(zip_data))
        
        # Parse the zip file
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            # Parse trips.txt for headsigns
            if 'trips.txt' in zip_file.namelist():
                await self._parse_trips(zip_file)
            
            # Parse routes.txt for route names
            if 'routes.txt' in zip_file.namelist():
                await self._parse_routes(zip_file)
            
            # Parse stops.txt for stop names
            if 'stops.txt' in zip_file.namelist():
                await self._parse_stops(zip_file)
        
        _LOGGER.info(
            "Loaded %d trip headsigns, %d routes, %d stops",
            len(self.trip_headsigns),
            len(self.route_names),
            len(self.stop_names)
        )

    async def _parse_trips(self, zip_file: zipfile.ZipFile):
        """Parse trips.txt to get trip_id -> headsign mapping."""
        with zip_file.open('trips.txt') as f:
            text_data = io.TextIOWrapper(f, encoding='utf-8-sig')
            reader = csv.DictReader(text_data)
            
            for row in reader:
                trip_id = row.get('trip_id', '').strip()
                headsign = row.get('trip_headsign', '').strip()
                
                if trip_id and headsign:
                    self.trip_headsigns[trip_id] = headsign

    async def _parse_routes(self, zip_file: zipfile.ZipFile):
        """Parse routes.txt to get route_id -> route_name mapping."""
        with zip_file.open('routes.txt') as f:
            text_data = io.TextIOWrapper(f, encoding='utf-8-sig')
            reader = csv.DictReader(text_data)
            
            for row in reader:
                route_id = row.get('route_id', '').strip()
                route_long_name = row.get('route_long_name', '').strip()
                route_short_name = row.get('route_short_name', '').strip()
                
                if route_id:
                    # Prefer long name, fallback to short name
                    self.route_names[route_id] = route_long_name or route_short_name

    async def _parse_stops(self, zip_file: zipfile.ZipFile):
        """Parse stops.txt to get stop_id -> stop_name mapping."""
        with zip_file.open('stops.txt') as f:
            text_data = io.TextIOWrapper(f, encoding='utf-8-sig')
            reader = csv.DictReader(text_data)
            
            for row in reader:
                stop_id = row.get('stop_id', '').strip()
                stop_name = row.get('stop_name', '').strip()
                
                if stop_id and stop_name:
                    self.stop_names[stop_id] = stop_name

    def get_trip_headsign(self, trip_id: str) -> str:
        """Get headsign for a trip_id."""
        return self.trip_headsigns.get(trip_id, "")

    def get_route_name(self, route_id: str) -> str:
        """Get route name for a route_id."""
        return self.route_names.get(route_id, "")

    def get_stop_name(self, stop_id: str) -> str:
        """Get stop name for a stop_id."""
        return self.stop_names.get(stop_id, "")