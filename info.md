# LIRR Filtered Departures

Real-time LIRR train departure information with advanced filtering for Home Assistant.

## Features

✨ **Multi-station support** - Configure multiple stations with different filters
🔍 **Smart filtering** - Filter by destination and route
📊 **Flexible sensors** - Create 1-20 departure sensors per station
⚡ **Real-time updates** - Live data from MTA every 60 seconds
📅 **Accurate info** - Uses GTFS static schedule for proper headsigns

## Quick Start

1. Add the integration
2. Enter your station name and stop ID
3. Optionally add direction/route filters
4. Choose number of departures to track

## Configuration

- **Station Name**: Friendly name (e.g., "Valley Stream Westbound")
- **Stop ID**: LIRR GTFS stop ID (e.g., "211")
- **Direction Filter**: Filter by destination using `|` (e.g., "Penn Station|Jamaica")
- **Route Filter**: Filter by route ID using `|` (e.g., "7|9")
- **Departure Limit**: Number of sensors (1-20)

## Finding Stop IDs

Common LIRR stations:
- Valley Stream: 211
- Jamaica: 139
- Penn Station: 110
- Hicksville: 26

Full list: [MTA Developers](https://new.mta.info/developers)

## Support

[GitHub Issues](https://github.com/lakerfan901/lirr-filtered-ha/issues)
