import pytest
from unittest.mock import MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.smarter_thermostat.const import DOMAIN
from custom_components.smarter_thermostat.config_flow import SmarterThermostatConfigFlow


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    return hass


class TestConfigFlow:
    @pytest.mark.asyncio
    async def test_step_user_form_shown(self):
        flow = SmarterThermostatConfigFlow()
        flow.hass = MagicMock()
        result = await flow.async_step_user(user_input=None)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_creates_entry(self):
        flow = SmarterThermostatConfigFlow()
        flow.hass = MagicMock()
        flow.hass.states = MagicMock()

        ac_state = MagicMock()
        ac_state.attributes = {"device_class": None}
        room_state = MagicMock()
        room_state.attributes = {"device_class": "temperature"}
        outside_state = MagicMock()
        outside_state.attributes = {"device_class": "temperature"}

        flow.hass.states.get = lambda eid: {
            "climate.test_ac": ac_state,
            "sensor.room_temp": room_state,
            "sensor.outside_temp": outside_state,
        }.get(eid)

        result = await flow.async_step_user(user_input={
            "name": "Living Room AC",
            "source_climate": "climate.test_ac",
            "room_sensor": "sensor.room_temp",
            "outside_sensor": "sensor.outside_temp",
        })
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Living Room AC"
        assert result["data"]["source_climate"] == "climate.test_ac"


class TestOptionsFlow:
    @pytest.mark.asyncio
    async def test_options_form_shown(self):
        from custom_components.smarter_thermostat.config_flow import SmarterThermostatOptionsFlow

        entry = MagicMock()
        entry.options = {}
        flow = SmarterThermostatOptionsFlow(entry)
        flow.hass = MagicMock()
        result = await flow.async_step_init(user_input=None)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_options_saved(self):
        from custom_components.smarter_thermostat.config_flow import SmarterThermostatOptionsFlow

        entry = MagicMock()
        entry.options = {}
        flow = SmarterThermostatOptionsFlow(entry)
        flow.hass = MagicMock()
        result = await flow.async_step_init(user_input={
            "calibration_weight": 0.5,
            "outside_temp_weight": 0.2,
            "dead_band": 1.5,
            "min_offset_change": 0.3,
            "update_interval": 90,
            "max_offset": 4.0,
            "min_mode_switch_interval": 120,
            "fan_only_enabled": False,
        })
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["calibration_weight"] == 0.5
        assert result["data"]["fan_only_enabled"] is False
