from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DEFAULT_CALIBRATION_WEIGHT,
    DEFAULT_OUTSIDE_TEMP_WEIGHT,
    DEFAULT_DEAD_BAND,
    DEFAULT_MIN_OFFSET_CHANGE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_MAX_OFFSET,
    DEFAULT_MIN_MODE_SWITCH_INTERVAL,
)

NUMBER_DEFINITIONS: list[dict] = [
    {
        "key": "calibration_weight",
        "name_suffix": "Calibration Weight",
        "min_value": 0.0,
        "max_value": 1.0,
        "step": 0.05,
        "coordinator_attr": "calibration_weight",
    },
    {
        "key": "outside_temp_weight",
        "name_suffix": "Outside Temp Weight",
        "min_value": 0.0,
        "max_value": 1.0,
        "step": 0.05,
        "coordinator_attr": "outside_temp_weight",
    },
    {
        "key": "dead_band",
        "name_suffix": "Dead Band",
        "min_value": 0.5,
        "max_value": 3.0,
        "step": 0.1,
        "coordinator_attr": "dead_band",
    },
    {
        "key": "min_offset_change",
        "name_suffix": "Min Offset Change",
        "min_value": 0.1,
        "max_value": 2.0,
        "step": 0.1,
        "coordinator_attr": "min_offset_change",
    },
    {
        "key": "update_interval",
        "name_suffix": "Update Interval",
        "min_value": 10,
        "max_value": 300,
        "step": 5,
        "coordinator_attr": "update_interval_seconds",
    },
    {
        "key": "max_offset",
        "name_suffix": "Max Offset",
        "min_value": 1.0,
        "max_value": 10.0,
        "step": 0.5,
        "coordinator_attr": "max_offset",
    },
    {
        "key": "min_mode_switch_interval",
        "name_suffix": "Min Mode Switch Interval",
        "min_value": 60,
        "max_value": 600,
        "step": 10,
        "coordinator_attr": "min_mode_switch_interval",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmarterThermostatNumber(coordinator, defn)
        for defn in NUMBER_DEFINITIONS
    ])


class SmarterThermostatNumber(NumberEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, definition: dict) -> None:
        self._coordinator = coordinator
        self._definition = definition
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{definition['key']}"
        self._attr_name = f"{coordinator.config_entry.title} {definition['name_suffix']}"
        self._attr_native_min_value = definition["min_value"]
        self._attr_native_max_value = definition["max_value"]
        self._attr_native_step = definition["step"]

    @property
    def native_value(self) -> float:
        return getattr(self._coordinator, self._definition["coordinator_attr"])

    async def async_set_native_value(self, value: float) -> None:
        setattr(self._coordinator, self._definition["coordinator_attr"], value)
