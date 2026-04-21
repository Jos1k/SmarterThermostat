import logging
import time
from datetime import timedelta
from typing import Optional

from homeassistant.components.climate import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calibration import calculate_offset, calculate_adjusted_target
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

_LOGGER = logging.getLogger(__name__)


class SmarterThermostatCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self._source_climate = entry.data[CONF_SOURCE_CLIMATE]
        self._room_sensor = entry.data[CONF_ROOM_SENSOR]
        self._outside_sensor = entry.data[CONF_OUTSIDE_SENSOR]

        self.enabled: bool = True
        self.fan_only_enabled: bool = entry.options.get(CONF_FAN_ONLY_ENABLED, DEFAULT_FAN_ONLY_ENABLED)
        self.calibration_weight: float = entry.options.get(CONF_CALIBRATION_WEIGHT, DEFAULT_CALIBRATION_WEIGHT)
        self.outside_temp_weight: float = entry.options.get(CONF_OUTSIDE_TEMP_WEIGHT, DEFAULT_OUTSIDE_TEMP_WEIGHT)
        self.dead_band: float = entry.options.get(CONF_DEAD_BAND, DEFAULT_DEAD_BAND)
        self.min_offset_change: float = entry.options.get(CONF_MIN_OFFSET_CHANGE, DEFAULT_MIN_OFFSET_CHANGE)
        self.update_interval_seconds: int = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        self.max_offset: float = entry.options.get(CONF_MAX_OFFSET, DEFAULT_MAX_OFFSET)
        self.min_mode_switch_interval: int = entry.options.get(
            CONF_MIN_MODE_SWITCH_INTERVAL, DEFAULT_MIN_MODE_SWITCH_INTERVAL
        )

        self.target_temp: Optional[float] = None
        self._last_offset: float = 0.0
        self._last_mode_switch_time: float = -self.min_mode_switch_interval
        self._previous_hvac_mode: Optional[str] = None
        self._in_deadband_fan_only: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.update_interval_seconds),
        )

    async def _async_update_data(self) -> dict:
        ac_state = self.hass.states.get(self._source_climate)
        room_state = self.hass.states.get(self._room_sensor)
        outside_state = self.hass.states.get(self._outside_sensor)

        if ac_state is None or room_state is None or outside_state is None:
            _LOGGER.warning("One or more entities unavailable, keeping last offset %.2f", self._last_offset)
            return self._build_result(self._last_offset, None)

        try:
            room_temp = float(room_state.state)
            ac_temp = float(ac_state.attributes.get("current_temperature", 0))
            outside_temp = float(outside_state.state)
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse sensor values, keeping last offset")
            return self._build_result(self._last_offset, None)

        if not self.enabled:
            self._last_offset = 0.0
            return self._build_result(0.0, None)

        new_offset = calculate_offset(
            room_temp=room_temp,
            ac_temp=ac_temp,
            outside_temp=outside_temp,
            calibration_weight=self.calibration_weight,
            outside_temp_weight=self.outside_temp_weight,
            max_offset=self.max_offset,
        )

        if abs(new_offset - self._last_offset) < self.min_offset_change:
            new_offset = self._last_offset

        self._last_offset = new_offset

        min_temp = ac_state.attributes.get("min_temp", 16.0)
        max_temp = ac_state.attributes.get("max_temp", 30.0)
        adjusted_target = None
        if self.target_temp is not None:
            adjusted_target = calculate_adjusted_target(
                target_temp=self.target_temp,
                offset=new_offset,
                min_temp=min_temp,
                max_temp=max_temp,
            )

        suggested_mode = self._evaluate_deadband(room_temp, ac_state.state)

        return self._build_result(new_offset, suggested_mode, adjusted_target, room_temp, ac_temp, outside_temp)

    def _evaluate_deadband(self, room_temp: float, current_hvac_mode: str) -> Optional[str]:
        if not self.fan_only_enabled or self.target_temp is None:
            return None

        in_deadband = abs(room_temp - self.target_temp) <= self.dead_band
        now = time.monotonic()
        can_switch = (now - self._last_mode_switch_time) >= self.min_mode_switch_interval

        if in_deadband and current_hvac_mode == HVACMode.COOL and not self._in_deadband_fan_only:
            if can_switch:
                self._previous_hvac_mode = current_hvac_mode
                self._in_deadband_fan_only = True
                self._last_mode_switch_time = now
                return HVACMode.FAN_ONLY
        elif not in_deadband and self._in_deadband_fan_only:
            if can_switch:
                self._in_deadband_fan_only = False
                self._last_mode_switch_time = now
                return self._previous_hvac_mode

        return None

    def _build_result(
        self,
        offset: float,
        suggested_hvac_mode: Optional[str],
        adjusted_target: Optional[float] = None,
        room_temp: Optional[float] = None,
        ac_temp: Optional[float] = None,
        outside_temp: Optional[float] = None,
    ) -> dict:
        return {
            "offset": offset,
            "adjusted_target": adjusted_target,
            "suggested_hvac_mode": suggested_hvac_mode,
            "room_temp": room_temp,
            "ac_temp": ac_temp,
            "outside_temp": outside_temp,
        }
