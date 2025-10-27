# LIRR Filtered Departures

A Home Assistant custom integration for real-time LIRR (Long Island Rail Road) train departure information with advanced filtering.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

## Features

- 🚆 **Real-time departures** - Live data from MTA GTFS-Realtime feeds
- 🎯 **Multi-station support** - Configure multiple stations with different filters
- 🔍 **Direction filtering** - Show only trains to specific destinations
- 🛤️ **Route filtering** - Filter by LIRR branch/route number
- 📊 **Flexible sensors** - Create 1-20 departure sensors per station
- 📅 **Accurate headsigns** - Uses GTFS static schedule for proper destination names
- ⚙️ **Easy management** - Add/edit/delete stations through the UI

## Installation

### Via HACS (Recommended)

1. Open **HACS** in your Home Assistant
2. Click the **3 dots** menu (top right)
3. Select **Custom repositories**
4. Add this repository:
   - **URL:** `https://github.com/lakerfan901/lirr-filtered-ha`
   - **Category:** Integration
5. Click **Add**
6. Search for "LIRR Filtered Departures" in HACS
7. Click **Download**
8. **Restart Home Assistant**
9. Add integration: **Settings → Devices & Services → Add Integration → LIRR Filtered Departures**

### Manual Installation

1. Download the latest release
2. Copy `custom_components/lirr_filtered` to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add integration through the UI

## Configuration

### Initial Setup

1. **Settings → Devices & Services → Add Integration**
2. Search for **"LIRR Filtered Departures"**
3. Configure your first station:
   - **Station Name**: Friendly name (e.g., "Valley Stream Westbound")
   - **Stop ID**: GTFS stop ID (e.g., "211" for Valley Stream)
   - **Direction Filter** (optional): Filter by destination using `|` separator
     - Example: `Penn Station|Jamaica`
   - **Route Filter** (optional): Filter by route ID using `|` separator
     - Example: `7|9`
   - **Departure Limit**: Number of departure sensors (1-20)
4. Choose to add more stations or finish

### Managing Stations

Edit your configuration anytime:
1. **Settings → Devices & Services → LIRR Filtered Departures**
2. Click **Configure**
3. Choose:
   - **Add new station** - Add another filtered view
   - **Edit existing station** - Modify filters
   - **Delete station** - Remove a station

## Finding Stop IDs

LIRR stop IDs can be found in the [MTA GTFS Static Feed](https://new.mta.info/developers).

Common stations:
- Valley Stream: `211`
- Jamaica: `139`
- Penn Station: `110`
- Hicksville: `26`
- Ronkonkoma: `67`

## Sensor Attributes

Each departure sensor provides:
- **State**: Minutes until departure
- **headsign**: Destination (e.g., "Penn Station")
- **departure_time**: Scheduled time (e.g., "09:45 PM")
- **route_id**: LIRR route number
- **trip_id**: Unique trip identifier
- **minutes_until**: Minutes until departure
- **stop_id**: Station stop ID
- **direction_filter**: Applied direction filter
- **route_filter**: Applied route filter

## Example Use Cases

### Westbound and Eastbound Trains
```yaml
Station 1: Valley Stream Westbound
- Stop ID: 211
- Direction Filter: Penn Station|Jamaica
- Sensors: 8 departures

Station 2: Valley Stream Eastbound
- Stop ID: 211
- Direction Filter: Far Rockaway|Long Beach
- Sensors: 8 departures
```

### Specific Routes Only
```yaml
Station: Hicksville
- Stop ID: 26
- Route Filter: 7
- Shows only Oyster Bay branch trains
```

## Support

- **Issues**: [GitHub Issues](https://github.com/lakerfan901/lirr-filtered-ha/issues)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

## Credits

Created for personal use. Uses MTA's GTFS Realtime feeds.

## License

MIT License
