import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from homeassistant.components.climate import (
    HVACMode,
    HVACAction,
    ClimateEntityFeature,
)
from homeassistant.const import UnitOfTemperature

from custom_components.smarter_thermostat.climate import SmarterThermostatClimate
from custom_components.smarter_thermostat.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator(mock_ac_state):
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry"
    coordinator.config_entry.title = "Living Room AC"
    coordinator.config_entry.data = {
        "source_climate": "climate.test_ac",
        "room_sensor": "sensor.room_temp",
        "outside_sensor": "sensor.outside_temp",
    }
    coordinator.data = {
        "offset": 1.6,
        "adjusted_target": 22.4,
        "suggested_hvac_mode": None,
        "room_temp": 26.0,
        "ac_temp": 24.0,
        "outside_temp": 35.0,
    }
    coordinator.enabled = True
    coordinator.target_temp = 24.0
    coordinator.hass = MagicMock()
    coordinator.hass.states.get = MagicMock(return_value=mock_ac_state)
    coordinator.hass.services = MagicMock()
    coordinator.hass.services.async_call = AsyncMock()
    return coordinator


class TestClimateProperties:
    def test_name(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.name == "Living Room AC"

    def test_unique_id(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.unique_id == "test_entry_climate"

    def test_current_temperature_from_room_sensor(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.current_temperature == 26.0

    def test_current_temperature_passthrough_when_disabled(self, mock_coordinator, mock_ac_state):
        mock_coordinator.enabled = False
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.current_temperature == mock_ac_state.attributes["current_temperature"]

    def test_target_temperature(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.target_temperature == 24.0

    def test_hvac_modes_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.hvac_modes == mock_ac_state.attributes["hvac_modes"]

    def test_preset_modes_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.preset_modes == mock_ac_state.attributes["preset_modes"]

    def test_fan_modes_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.fan_modes == mock_ac_state.attributes["fan_modes"]

    def test_swing_modes_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.swing_modes == mock_ac_state.attributes["swing_modes"]

    def test_min_max_temp_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.min_temp == mock_ac_state.attributes["min_temp"]
        assert climate.max_temp == mock_ac_state.attributes["max_temp"]

    def test_hvac_mode_from_ac(self, mock_coordinator, mock_ac_state):
        climate = SmarterThermostatClimate(mock_coordinator)
        assert climate.hvac_mode == mock_ac_state.state

    def test_extra_state_attributes(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        attrs = climate.extra_state_attributes
        assert attrs["calibration_offset"] == 1.6
        assert attrs["adjusted_target"] == 22.4
        assert attrs["ac_temperature"] == 24.0
        assert attrs["outside_temperature"] == 35.0


class TestClimateCommands:
    @pytest.mark.asyncio
    async def test_set_temperature_stores_target_and_calls_ac(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        await climate.async_set_temperature(temperature=24.0)
        assert mock_coordinator.target_temp == 24.0
        mock_coordinator.hass.services.async_call.assert_called_once()
        call_args = mock_coordinator.hass.services.async_call.call_args
        assert call_args[0][0] == "climate"
        assert call_args[0][1] == "set_temperature"

    @pytest.mark.asyncio
    async def test_set_hvac_mode_proxied(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        await climate.async_set_hvac_mode(HVACMode.HEAT)
        mock_coordinator.hass.services.async_call.assert_called_once()
        call_args = mock_coordinator.hass.services.async_call.call_args
        assert call_args[0][1] == "set_hvac_mode"

    @pytest.mark.asyncio
    async def test_set_fan_mode_proxied(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        await climate.async_set_fan_mode("high")
        mock_coordinator.hass.services.async_call.assert_called_once()
        call_args = mock_coordinator.hass.services.async_call.call_args
        assert call_args[0][1] == "set_fan_mode"

    @pytest.mark.asyncio
    async def test_set_swing_mode_proxied(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        await climate.async_set_swing_mode("vertical")
        mock_coordinator.hass.services.async_call.assert_called_once()
        call_args = mock_coordinator.hass.services.async_call.call_args
        assert call_args[0][1] == "set_swing_mode"

    @pytest.mark.asyncio
    async def test_set_preset_mode_proxied(self, mock_coordinator):
        climate = SmarterThermostatClimate(mock_coordinator)
        await climate.async_set_preset_mode("eco")
        mock_coordinator.hass.services.async_call.assert_called_once()
        call_args = mock_coordinator.hass.services.async_call.call_args
        assert call_args[0][1] == "set_preset_mode"
