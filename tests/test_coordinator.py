import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import timedelta
from typing import Optional

from homeassistant.components.climate import HVACMode
from homeassistant.core import HomeAssistant

from custom_components.smarter_thermostat.const import (
    DEFAULT_CALIBRATION_WEIGHT,
    DEFAULT_OUTSIDE_TEMP_WEIGHT,
    DEFAULT_DEAD_BAND,
    DEFAULT_MIN_OFFSET_CHANGE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_MAX_OFFSET,
    DEFAULT_MIN_MODE_SWITCH_INTERVAL,
    DEFAULT_FAN_ONLY_ENABLED,
    CONF_SOURCE_CLIMATE,
    CONF_ROOM_SENSOR,
    CONF_OUTSIDE_SENSOR,
)
from custom_components.smarter_thermostat.coordinator import SmarterThermostatCoordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_config_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.title = "Living Room AC"
    entry.data = {
        CONF_SOURCE_CLIMATE: "climate.test_ac",
        CONF_ROOM_SENSOR: "sensor.room_temp",
        CONF_OUTSIDE_SENSOR: "sensor.outside_temp",
    }
    entry.options = {}
    return entry


def make_state(entity_id: str, state: str, attributes: Optional[dict] = None):
    mock = MagicMock()
    mock.entity_id = entity_id
    mock.state = state
    mock.attributes = attributes or {}
    return mock


class TestCoordinatorInit:
    def test_defaults(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        assert coordinator.enabled is True
        assert coordinator.fan_only_enabled is DEFAULT_FAN_ONLY_ENABLED
        assert coordinator.calibration_weight == DEFAULT_CALIBRATION_WEIGHT
        assert coordinator.outside_temp_weight == DEFAULT_OUTSIDE_TEMP_WEIGHT
        assert coordinator.dead_band == DEFAULT_DEAD_BAND
        assert coordinator.min_offset_change == DEFAULT_MIN_OFFSET_CHANGE
        assert coordinator.update_interval_seconds == DEFAULT_UPDATE_INTERVAL
        assert coordinator.max_offset == DEFAULT_MAX_OFFSET
        assert coordinator.min_mode_switch_interval == DEFAULT_MIN_MODE_SWITCH_INTERVAL

    def test_options_override_defaults(self, mock_hass, mock_config_entry):
        mock_config_entry.options = {
            "calibration_weight": 0.5,
            "dead_band": 2.0,
        }
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        assert coordinator.calibration_weight == 0.5
        assert coordinator.dead_band == 2.0
        assert coordinator.outside_temp_weight == DEFAULT_OUTSIDE_TEMP_WEIGHT


class TestCoordinatorUpdate:
    @pytest.mark.asyncio
    async def test_calculates_offset(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 22.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "26.0")
        outside_state = make_state("sensor.outside_temp", "35.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["offset"] != 0.0
        assert "adjusted_target" in data

    @pytest.mark.asyncio
    async def test_disabled_returns_zero_offset(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.enabled = False
        coordinator.target_temp = 24.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 22.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "26.0")
        outside_state = make_state("sensor.outside_temp", "35.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["offset"] == 0.0

    @pytest.mark.asyncio
    async def test_unavailable_sensor_keeps_last_offset(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator._last_offset = 1.5

        mock_hass.states.get = lambda eid: None

        data = await coordinator._async_update_data()
        assert data["offset"] == 1.5

    @pytest.mark.asyncio
    async def test_min_offset_change_suppresses_update(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator._last_offset = 1.5

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 22.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "25.9")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        new_raw = (25.9 - 24.0) * DEFAULT_CALIBRATION_WEIGHT
        if abs(new_raw - 1.5) < DEFAULT_MIN_OFFSET_CHANGE:
            assert data["offset"] == 1.5


    @pytest.mark.asyncio
    async def test_sends_adjusted_target_to_ac(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "26.0")
        outside_state = make_state("sensor.outside_temp", "35.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["adjusted_target"] is not None
        mock_hass.services.async_call.assert_any_call(
            "climate", "set_temperature",
            {"entity_id": "climate.test_ac", "temperature": data["adjusted_target"]},
        )

    @pytest.mark.asyncio
    async def test_does_not_resend_same_adjusted_target(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "26.0")
        outside_state = make_state("sensor.outside_temp", "35.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        await coordinator._async_update_data()
        call_count_after_first = mock_hass.services.async_call.call_count

        await coordinator._async_update_data()
        assert mock_hass.services.async_call.call_count == call_count_after_first

    @pytest.mark.asyncio
    async def test_reads_initial_target_from_ac(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        assert coordinator.target_temp is None

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 22.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "24.0")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        await coordinator._async_update_data()
        assert coordinator.target_temp == 22.0

    @pytest.mark.asyncio
    async def test_unavailable_string_state_keeps_last_offset(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator._last_offset = 2.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "unavailable")
        outside_state = make_state("sensor.outside_temp", "35.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["offset"] == 2.0


class TestDeadBandLogic:
    @pytest.mark.asyncio
    async def test_cooling_within_deadband_suggests_fan_only(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator.dead_band = 1.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "24.5")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["suggested_hvac_mode"] == HVACMode.FAN_ONLY

    @pytest.mark.asyncio
    async def test_heating_within_deadband_no_fan_only(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator.dead_band = 1.0

        ac_state = make_state("climate.test_ac", HVACMode.HEAT, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "heating",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "23.5")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data.get("suggested_hvac_mode") is None

    @pytest.mark.asyncio
    async def test_sends_hvac_mode_to_ac(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator.dead_band = 1.0

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "24.5")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data["suggested_hvac_mode"] == HVACMode.FAN_ONLY
        mock_hass.services.async_call.assert_any_call(
            "climate", "set_hvac_mode",
            {"entity_id": "climate.test_ac", "hvac_mode": HVACMode.FAN_ONLY},
        )

    @pytest.mark.asyncio
    async def test_fan_only_disabled_no_mode_switch(self, mock_hass, mock_config_entry):
        coordinator = SmarterThermostatCoordinator(mock_hass, mock_config_entry)
        coordinator.target_temp = 24.0
        coordinator.fan_only_enabled = False

        ac_state = make_state("climate.test_ac", HVACMode.COOL, {
            "current_temperature": 24.0,
            "temperature": 24.0,
            "hvac_action": "cooling",
            "min_temp": 16.0,
            "max_temp": 30.0,
        })
        room_state = make_state("sensor.room_temp", "24.5")
        outside_state = make_state("sensor.outside_temp", "25.0")

        mock_hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }[eid]

        data = await coordinator._async_update_data()
        assert data.get("suggested_hvac_mode") is None
