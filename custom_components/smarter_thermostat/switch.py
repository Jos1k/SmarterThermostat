from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmarterThermostatSwitch(coordinator),
        SmarterThermostatFanOnlySwitch(coordinator),
    ])


class SmarterThermostatSwitch(SwitchEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_enabled"
        self._attr_name = coordinator.config_entry.title

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def is_on(self) -> bool:
        return self._coordinator.enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.enabled = True
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.enabled = False
        await self._coordinator.async_request_refresh()


class SmarterThermostatFanOnlySwitch(SwitchEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_fan_only_enabled"
        self._attr_name = f"{coordinator.config_entry.title} Fan-Only Mode"

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def is_on(self) -> bool:
        return self._coordinator.fan_only_enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.fan_only_enabled = True

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.fan_only_enabled = False
