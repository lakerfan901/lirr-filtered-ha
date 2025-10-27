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
    CONF_DIRECTION_FILTERS,
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
        self.station_name = None
        self.stop_id = None
        self.departure_limit = DEFAULT_DEPARTURE_LIMIT
        self.direction_filters = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step - station configuration."""
        if user_input is not None:
            self.station_name = user_input[CONF_STATION_NAME]
            self.stop_id = user_input[CONF_STOP_ID]
            self.departure_limit = int(user_input.get(CONF_DEPARTURE_LIMIT, DEFAULT_DEPARTURE_LIMIT))

            return await self.async_step_add_direction_filter()

        data_schema = vol.Schema({
            vol.Required(CONF_STATION_NAME): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_STOP_ID): TextSelector(
                TextSelectorConfig(multiline=False)
            ),
            vol.Required(CONF_DEPARTURE_LIMIT, default=DEFAULT_DEPARTURE_LIMIT): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders={
                "station_name_example": "e.g., Valley Stream",
                "stop_id_example": "e.g., 211",
            }
        )

    async def async_step_add_direction_filter(self, user_input: dict[str, Any] | None = None):
        """Add a direction filter."""
        if user_input is not None:
            filter_name = user_input.get("direction_filter_name", "").strip()

            if filter_name:
                self.direction_filters.append(filter_name)

            if user_input.get("add_another"):
                # Add another filter
                return await self.async_step_add_direction_filter()
            else:
                # Finish configuration
                if not self.direction_filters:
                    # No filters added, add a default one
                    self.direction_filters = ["All Trains"]

                station_config = {
                    CONF_STATION_NAME: self.station_name,
                    CONF_STOP_ID: self.stop_id,
                    CONF_DEPARTURE_LIMIT: self.departure_limit,
                    CONF_DIRECTION_FILTERS: self.direction_filters,
                }

                title = f"LIRR {self.station_name}"
                return self.async_create_entry(
                    title=title,
                    data={CONF_STATIONS: [station_config]},
                )

        # Build description showing current filters
        if self.direction_filters:
            filters_summary = "\n".join([f"{i+1}. {f}" for i, f in enumerate(self.direction_filters)])
            description = f"Station: {self.station_name}\nFilters added:\n{filters_summary}\n\nAdd another direction filter or finish."
        else:
            description = f"Station: {self.station_name}\n\nAdd direction filters (e.g., 'Penn Station', 'Grand Central').\nIf no filters are added, 'All Trains' will be used."

        return self.async_show_form(
            step_id="add_direction_filter",
            data_schema=vol.Schema({
                vol.Optional("direction_filter_name", default=""): TextSelector(
                    TextSelectorConfig(multiline=False)
                ),
                vol.Required("add_another", default=False): bool,
            }),
            description_placeholders={
                "description": description,
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
        self.current_station_idx = 0  # We only support one station now
        self.direction_filters = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if not self.stations:
            return self.async_abort(reason="no_stations")

        station = self.stations[self.current_station_idx]
        self.direction_filters = list(station.get(CONF_DIRECTION_FILTERS, ["All Trains"]))

        if user_input is not None:
            if user_input.get("action") == "edit_filters":
                return await self.async_step_edit_filters()
            elif user_input.get("action") == "edit_station":
                return await self.async_step_edit_station()
            else:
                return self.async_create_entry(title="", data={})

        filters_summary = "\n".join([f"{i+1}. {f}" for i, f in enumerate(self.direction_filters)])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "edit_station": "Edit station configuration",
                    "edit_filters": "Edit direction filters",
                    "done": "Done",
                }),
            }),
            description_placeholders={
                "station_name": station[CONF_STATION_NAME],
                "stop_id": station[CONF_STOP_ID],
                "departure_limit": str(station[CONF_DEPARTURE_LIMIT]),
                "filters": filters_summary,
            }
        )

    async def async_step_edit_station(self, user_input: dict[str, Any] | None = None):
        """Edit station configuration."""
        if user_input is not None:
            self.stations[self.current_station_idx][CONF_STATION_NAME] = user_input[CONF_STATION_NAME]
            self.stations[self.current_station_idx][CONF_STOP_ID] = user_input[CONF_STOP_ID]
            self.stations[self.current_station_idx][CONF_DEPARTURE_LIMIT] = int(user_input[CONF_DEPARTURE_LIMIT])

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
            vol.Required(CONF_DEPARTURE_LIMIT, default=station[CONF_DEPARTURE_LIMIT]): NumberSelector(
                NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="edit_station",
            data_schema=data_schema,
        )

    async def async_step_edit_filters(self, user_input: dict[str, Any] | None = None):
        """Edit direction filters."""
        if user_input is not None:
            if user_input.get("action") == "add":
                return await self.async_step_add_filter()
            elif user_input.get("action") == "delete":
                return await self.async_step_delete_filter()
            else:
                # Save and exit
                self.stations[self.current_station_idx][CONF_DIRECTION_FILTERS] = self.direction_filters

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={CONF_STATIONS: self.stations},
                )

                return self.async_create_entry(title="", data={})

        filters_summary = "\n".join([f"{i+1}. {f}" for i, f in enumerate(self.direction_filters)])

        return self.async_show_form(
            step_id="edit_filters",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In({
                    "add": "Add new filter",
                    "delete": "Delete filter",
                    "done": "Done",
                }),
            }),
            description_placeholders={
                "filters": filters_summary,
            }
        )

    async def async_step_add_filter(self, user_input: dict[str, Any] | None = None):
        """Add a new direction filter."""
        if user_input is not None:
            filter_name = user_input.get("direction_filter_name", "").strip()
            if filter_name and filter_name not in self.direction_filters:
                self.direction_filters.append(filter_name)

            return await self.async_step_edit_filters()

        return self.async_show_form(
            step_id="add_filter",
            data_schema=vol.Schema({
                vol.Required("direction_filter_name"): TextSelector(
                    TextSelectorConfig(multiline=False)
                ),
            }),
        )

    async def async_step_delete_filter(self, user_input: dict[str, Any] | None = None):
        """Delete a direction filter."""
        if user_input is not None:
            filter_idx = int(user_input["filter_idx"])
            del self.direction_filters[filter_idx]

            return await self.async_step_edit_filters()

        if not self.direction_filters:
            return await self.async_step_edit_filters()

        filter_options = {
            str(i): f
            for i, f in enumerate(self.direction_filters)
        }

        return self.async_show_form(
            step_id="delete_filter",
            data_schema=vol.Schema({
                vol.Required("filter_idx"): vol.In(filter_options),
            }),
        )
