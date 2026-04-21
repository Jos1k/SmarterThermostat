from typing import Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_SOURCE_CLIMATE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmarterThermostatClimate(coordinator)])


class SmarterThermostatClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = False
    _enable_turn_on_turn_off_backwards_compat = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._source_entity_id = coordinator.config_entry.data[CONF_SOURCE_CLIMATE]
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"
        self._attr_name = coordinator.config_entry.title

    @property
    def _ac_state(self):
        return self.coordinator.hass.states.get(self._source_entity_id)

    @property
    def supported_features(self) -> ClimateEntityFeature:
        ac = self._ac_state
        if ac is None:
            return ClimateEntityFeature(0)
        return ClimateEntityFeature(ac.attributes.get("supported_features", 0))

    @property
    def hvac_modes(self) -> list:
        ac = self._ac_state
        if ac is None:
            return []
        return ac.attributes.get("hvac_modes", [])

    @property
    def hvac_mode(self) -> Optional[HVACMode]:
        ac = self._ac_state
        if ac is None:
            return None
        return ac.state

    @property
    def hvac_action(self):
        ac = self._ac_state
        if ac is None:
            return None
        return ac.attributes.get("hvac_action")

    @property
    def current_temperature(self) -> Optional[float]:
        if not self.coordinator.enabled:
            ac = self._ac_state
            return ac.attributes.get("current_temperature") if ac else None
        data = self.coordinator.data
        if data and data.get("room_temp") is not None:
            return data["room_temp"]
        ac = self._ac_state
        return ac.attributes.get("current_temperature") if ac else None

    @property
    def target_temperature(self) -> Optional[float]:
        return self.coordinator.target_temp

    @property
    def min_temp(self) -> float:
        ac = self._ac_state
        return ac.attributes.get("min_temp", 16.0) if ac else 16.0

    @property
    def max_temp(self) -> float:
        ac = self._ac_state
        return ac.attributes.get("max_temp", 30.0) if ac else 30.0

    @property
    def preset_modes(self) -> Optional[list[str]]:
        ac = self._ac_state
        return ac.attributes.get("preset_modes") if ac else None

    @property
    def preset_mode(self) -> Optional[str]:
        ac = self._ac_state
        return ac.attributes.get("preset_mode") if ac else None

    @property
    def fan_modes(self) -> Optional[list[str]]:
        ac = self._ac_state
        return ac.attributes.get("fan_modes") if ac else None

    @property
    def fan_mode(self) -> Optional[str]:
        ac = self._ac_state
        return ac.attributes.get("fan_mode") if ac else None

    @property
    def swing_modes(self) -> Optional[list[str]]:
        ac = self._ac_state
        return ac.attributes.get("swing_modes") if ac else None

    @property
    def swing_mode(self) -> Optional[str]:
        ac = self._ac_state
        return ac.attributes.get("swing_mode") if ac else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            "calibration_offset": data.get("offset", 0.0),
            "adjusted_target": data.get("adjusted_target"),
            "ac_temperature": data.get("ac_temp"),
            "outside_temperature": data.get("outside_temp"),
        }

    async def _async_call_ac_service(self, service: str, **kwargs) -> None:
        kwargs[ATTR_ENTITY_ID] = self._source_entity_id
        await self.coordinator.hass.services.async_call("climate", service, kwargs)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self.coordinator.target_temp = temp
            data = self.coordinator.data or {}
            offset = data.get("offset", 0.0)
            adjusted = temp - offset
            adjusted = max(self.min_temp, min(self.max_temp, adjusted))
            await self._async_call_ac_service("set_temperature", **{ATTR_TEMPERATURE: adjusted})

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self._async_call_ac_service("set_hvac_mode", hvac_mode=hvac_mode)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._async_call_ac_service("set_fan_mode", fan_mode=fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._async_call_ac_service("set_swing_mode", swing_mode=swing_mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._async_call_ac_service("set_preset_mode", preset_mode=preset_mode)

    @property
    def should_poll(self) -> bool:
        return False
