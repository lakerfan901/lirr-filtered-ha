"""Config flow for LIRR Filtered integration."""

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_DEPARTURE_LIMIT,
    CONF_DIRECTION_FILTER,
    CONF_ROUTE_FILTER,
    CONF_STATION_NAME,
    CONF_STATIONS,
    CONF_STOP_ID,
    DEFAULT_DEPARTURE_LIMIT,
    DOMAIN,
)


class LIRRFilteredConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LIRR Filtered."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.stations = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        return await self.async_step_add_station(user_input)

    async def async_step_add_station(self, user_input: dict[str, Any] | None = None):
        """Add a station configuration."""
        errors = {}

        if user_input is not None:
            # Add this station to the list
            station_config = {
                CONF_STATION_NAME: user_input[CONF_STATION_NAME],
                CONF_STOP_ID: user_input[CONF_STOP_ID],
                CONF_DIRECTION_FILTER: user_input.get(CONF_DIRECTION_FILTER, ""),
                CONF_ROUTE_FILTER: user_input.get(CONF_ROUTE_FILTER, ""),
                CONF_DEPARTURE_LIMIT: int(user_input.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT)),
            }
            self.stations.append(station_config)
            
            # Ask if they want to add another station
            return await self.async_step_add_another()

        data_schema = vol.Schema({
            vol.Required(CONF_STATION_NAME): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_STOP_ID): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Optional(CONF_DIRECTION_FILTER, default=""): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Optional(CONF_ROUTE_FILTER, default=""): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_DEPARTURE_LIMIT, default=DEFAULT_DEPARTURE_LIMIT): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        })

        station_count = len(self.stations)
        description = "Configure your LIRR station and filters."
        if station_count > 0:
            description = f"You have added {station_count} station(s). Add another station."

        return self.async_show_form(
            step_id="add_station",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "description": description,
            }
        )

    async def async_step_add_another(self, user_input: dict[str, Any] | None = None):
        """Ask if user wants to add another station."""
        if user_input is not None:
            if user_input.get("add_another"):
                return await self.async_step_add_station()
            else:
                # Create the entry with all stations
                title = f"LIRR ({len(self.stations)} station{'s' if len(self.stations) > 1 else ''})"
                return self.async_create_entry(
                    title=title,
                    data={CONF_STATIONS: self.stations},
                )

        # Show summary of added stations
        stations_summary = "\n".join([
            f"{i+1}. {s[CONF_STATION_NAME]} (Stop: {s[CONF_STOP_ID]})"
            for i, s in enumerate(self.stations)
        ])

        return self.async_show_form(
            step_id="add_another",
            data_schema=vol.Schema({
                vol.Required("add_another", default=False): bool,
            }),
            description_placeholders={
                "stations_summary": stations_summary,
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return LIRROptionsFlowHandler(config_entry)


class LIRROptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for LIRR Filtered."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.stations = list(config_entry.data.get(CONF_STATIONS, []))
        self.current_station_idx = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options - show list of stations."""
        if user_input is not None:
            if user_input.get("action") == "add":
                return await self.async_step_add_station()
            elif user_input.get("action") == "edit":
                return await self.async_step_select_station_to_edit()
            elif user_input.get("action") == "delete":
                return await self.async_step_select_station_to_delete()
            else:
                return self.async_create_entry(title="", data={})

        stations_summary = "\n".join([
            f"{i+1}. {s[CONF_STATION_NAME]} (Stop: {s[CONF_STOP_ID]})"
            for i, s in enumerate(self.stations)
        ])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "add": "Add new station",
                    "edit": "Edit existing station",
                    "delete": "Delete station",
                    "done": "Done",
                }),
            }),
            description_placeholders={
                "stations": stations_summary,
            }
        )

    async def async_step_add_station(self, user_input: dict[str, Any] | None = None):
        """Add a new station."""
        if user_input is not None:
            station_config = {
                CONF_STATION_NAME: user_input[CONF_STATION_NAME],
                CONF_STOP_ID: user_input[CONF_STOP_ID],
                CONF_DIRECTION_FILTER: user_input.get(CONF_DIRECTION_FILTER, ""),
                CONF_ROUTE_FILTER: user_input.get(CONF_ROUTE_FILTER, ""),
                CONF_DEPARTURE_LIMIT: int(user_input.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT)),
            }
            self.stations.append(station_config)
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_STATIONS: self.stations},
            )
            
            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema({
            vol.Required(CONF_STATION_NAME): TextSelector(TextSelectorConfig(multiline=False)),
            vol.Required(CONF_STOP_ID): TextSelector(TextSelectorConfig(multiline=False)),
            vol.Optional(CONF_DIRECTION_FILTER, default=""): TextSelector(TextSelectorConfig(multiline=False)),
            vol.Optional(CONF_ROUTE_FILTER, default=""): TextSelector(TextSelectorConfig(multiline=False)),
            vol.Required(CONF_DEPARTURE_LIMIT, default=DEFAULT_DEPARTURE_LIMIT): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="add_station",
            data_schema=data_schema,
        )

    async def async_step_select_station_to_edit(self, user_input: dict[str, Any] | None = None):
        """Select which station to edit."""
        if user_input is not None:
            self.current_station_idx = user_input["station_idx"]
            return await self.async_step_edit_station()

        station_options = {
            str(i): f"{s[CONF_STATION_NAME]} (Stop: {s[CONF_STOP_ID]})"
            for i, s in enumerate(self.stations)
        }

        return self.async_show_form(
            step_id="select_station_to_edit",
            data_schema=vol.Schema({
                vol.Required("station_idx"): vol.In(station_options),
            }),
        )

    async def async_step_edit_station(self, user_input: dict[str, Any] | None = None):
        """Edit a station."""
        if user_input is not None:
            self.stations[self.current_station_idx] = {
                CONF_STATION_NAME: user_input[CONF_STATION_NAME],
                CONF_STOP_ID: user_input[CONF_STOP_ID],
                CONF_DIRECTION_FILTER: user_input.get(CONF_DIRECTION_FILTER, ""),
                CONF_ROUTE_FILTER: user_input.get(CONF_ROUTE_FILTER, ""),
                CONF_DEPARTURE_LIMIT: int(user_input.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT)),
            }
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_STATIONS: self.stations},
            )
            
            return self.async_create_entry(title="", data={})

        station = self.stations[self.current_station_idx]

        data_schema = vol.Schema({
            vol.Required(CONF_STATION_NAME, default=station[CONF_STATION_NAME]): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_STOP_ID, default=station[CONF_STOP_ID]): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Optional(CONF_DIRECTION_FILTER, default=station.get(CONF_DIRECTION_FILTER, "")): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Optional(CONF_ROUTE_FILTER, default=station.get(CONF_ROUTE_FILTER, "")): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_DEPARTURE_LIMIT, default=station.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT)): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="edit_station",
            data_schema=data_schema,
        )

    async def async_step_select_station_to_delete(self, user_input: dict[str, Any] | None = None):
        """Select which station to delete."""
        if user_input is not None:
            station_idx = int(user_input["station_idx"])
            del self.stations[station_idx]
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_STATIONS: self.stations},
            )
            
            return self.async_create_entry(title="", data={})

        station_options = {
            str(i): f"{s[CONF_STATION_NAME]} (Stop: {s[CONF_STOP_ID]})"
            for i, s in enumerate(self.stations)
        }

        return self.async_show_form(
            step_id="select_station_to_delete",
            data_schema=vol.Schema({
                vol.Required("station_idx"): vol.In(station_options),
            }),
        )