import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_SOURCE_CLIMATE,
    CONF_ROOM_SENSOR,
    CONF_OUTSIDE_SENSOR,
    CONF_CALIBRATION_WEIGHT,
    CONF_OUTSIDE_TEMP_WEIGHT,
    CONF_DEAD_BAND,
    CONF_MIN_OFFSET_CHANGE,
    CONF_UPDATE_INTERVAL,
    CONF_MAX_OFFSET,
    CONF_MIN_MODE_SWITCH_INTERVAL,
    CONF_FAN_ONLY_ENABLED,
    DEFAULT_CALIBRATION_WEIGHT,
    DEFAULT_OUTSIDE_TEMP_WEIGHT,
    DEFAULT_DEAD_BAND,
    DEFAULT_MIN_OFFSET_CHANGE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_MAX_OFFSET,
    DEFAULT_MIN_MODE_SWITCH_INTERVAL,
    DEFAULT_FAN_ONLY_ENABLED,
)

USER_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required(CONF_SOURCE_CLIMATE): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="climate"),
    ),
    vol.Required(CONF_ROOM_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature"),
    ),
    vol.Required(CONF_OUTSIDE_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature"),
    ),
})


def options_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required(
            CONF_CALIBRATION_WEIGHT,
            default=options.get(CONF_CALIBRATION_WEIGHT, DEFAULT_CALIBRATION_WEIGHT),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.0, max=1.0, step=0.05, mode="slider",
        )),
        vol.Required(
            CONF_OUTSIDE_TEMP_WEIGHT,
            default=options.get(CONF_OUTSIDE_TEMP_WEIGHT, DEFAULT_OUTSIDE_TEMP_WEIGHT),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.0, max=1.0, step=0.05, mode="slider",
        )),
        vol.Required(
            CONF_DEAD_BAND,
            default=options.get(CONF_DEAD_BAND, DEFAULT_DEAD_BAND),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.5, max=3.0, step=0.1, mode="slider",
        )),
        vol.Required(
            CONF_MIN_OFFSET_CHANGE,
            default=options.get(CONF_MIN_OFFSET_CHANGE, DEFAULT_MIN_OFFSET_CHANGE),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.1, max=2.0, step=0.1, mode="slider",
        )),
        vol.Required(
            CONF_UPDATE_INTERVAL,
            default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=10, max=300, step=5, mode="slider",
        )),
        vol.Required(
            CONF_MAX_OFFSET,
            default=options.get(CONF_MAX_OFFSET, DEFAULT_MAX_OFFSET),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=1.0, max=10.0, step=0.5, mode="slider",
        )),
        vol.Required(
            CONF_MIN_MODE_SWITCH_INTERVAL,
            default=options.get(CONF_MIN_MODE_SWITCH_INTERVAL, DEFAULT_MIN_MODE_SWITCH_INTERVAL),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=60, max=600, step=10, mode="slider",
        )),
        vol.Required(
            CONF_FAN_ONLY_ENABLED,
            default=options.get(CONF_FAN_ONLY_ENABLED, DEFAULT_FAN_ONLY_ENABLED),
        ): bool,
    })


class SmarterThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    CONF_SOURCE_CLIMATE: user_input[CONF_SOURCE_CLIMATE],
                    CONF_ROOM_SENSOR: user_input[CONF_ROOM_SENSOR],
                    CONF_OUTSIDE_SENSOR: user_input[CONF_OUTSIDE_SENSOR],
                },
            )
        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmarterThermostatOptionsFlow(config_entry)


class SmarterThermostatOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(self._config_entry.options),
        )
