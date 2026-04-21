import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
from types import ModuleType

# Mock homeassistant before any imports
if 'homeassistant' not in sys.modules or not hasattr(sys.modules.get('homeassistant'), '__path__'):
    # Create mock modules as proper namespace packages
    homeassistant = ModuleType('homeassistant')
    homeassistant_core = ModuleType('homeassistant.core')
    homeassistant_config_entries = ModuleType('homeassistant.config_entries')
    homeassistant_components = ModuleType('homeassistant.components')
    homeassistant_components_switch = ModuleType('homeassistant.components.switch')
    homeassistant_helpers = ModuleType('homeassistant.helpers')
    homeassistant_helpers_entity_platform = ModuleType('homeassistant.helpers.entity_platform')

    # Mock the classes
    class SwitchEntity:
        def async_write_ha_state(self):
            pass

    class HomeAssistant:
        pass

    class ConfigEntry:
        pass

    class AddEntitiesCallback:
        pass

    # Assign mocks
    homeassistant_components_switch.SwitchEntity = SwitchEntity
    homeassistant_core.HomeAssistant = HomeAssistant
    homeassistant_config_entries.ConfigEntry = ConfigEntry
    homeassistant_helpers_entity_platform.AddEntitiesCallback = AddEntitiesCallback

    # Register in sys.modules
    sys.modules['homeassistant'] = homeassistant
    sys.modules['homeassistant.core'] = homeassistant_core
    sys.modules['homeassistant.config_entries'] = homeassistant_config_entries
    sys.modules['homeassistant.components'] = homeassistant_components
    sys.modules['homeassistant.components.switch'] = homeassistant_components_switch
    sys.modules['homeassistant.helpers'] = homeassistant_helpers
    sys.modules['homeassistant.helpers.entity_platform'] = homeassistant_helpers_entity_platform

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.smarter_thermostat.const import (
    DOMAIN,
    CONF_FAN_ONLY_ENABLED,
    DEFAULT_FAN_ONLY_ENABLED,
)
from custom_components.smarter_thermostat.switch import (
    SmarterThermostatSwitch,
    SmarterThermostatFanOnlySwitch,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.title = "Living Room AC"
    coordinator.enabled = True
    coordinator.fan_only_enabled = DEFAULT_FAN_ONLY_ENABLED
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestSmarterThermostatSwitch:
    def test_initial_state_on(self, mock_coordinator):
        switch = SmarterThermostatSwitch(mock_coordinator)
        assert switch.is_on is True

    def test_name(self, mock_coordinator):
        switch = SmarterThermostatSwitch(mock_coordinator)
        assert switch.name == "Living Room AC"

    def test_unique_id(self, mock_coordinator):
        switch = SmarterThermostatSwitch(mock_coordinator)
        assert switch.unique_id == "test_entry_id_enabled"

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator):
        switch = SmarterThermostatSwitch(mock_coordinator)
        await switch.async_turn_off()
        assert mock_coordinator.enabled is False
        mock_coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator):
        switch = SmarterThermostatSwitch(mock_coordinator)
        mock_coordinator.enabled = False
        await switch.async_turn_on()
        assert mock_coordinator.enabled is True
        mock_coordinator.async_request_refresh.assert_called_once()


class TestSmarterThermostatFanOnlySwitch:
    def test_initial_state(self, mock_coordinator):
        switch = SmarterThermostatFanOnlySwitch(mock_coordinator)
        assert switch.is_on is True

    def test_name(self, mock_coordinator):
        switch = SmarterThermostatFanOnlySwitch(mock_coordinator)
        assert switch.name == "Living Room AC Fan-Only Mode"

    def test_unique_id(self, mock_coordinator):
        switch = SmarterThermostatFanOnlySwitch(mock_coordinator)
        assert switch.unique_id == "test_entry_id_fan_only_enabled"

    @pytest.mark.asyncio
    async def test_turn_off(self, mock_coordinator):
        switch = SmarterThermostatFanOnlySwitch(mock_coordinator)
        await switch.async_turn_off()
        assert mock_coordinator.fan_only_enabled is False

    @pytest.mark.asyncio
    async def test_turn_on(self, mock_coordinator):
        switch = SmarterThermostatFanOnlySwitch(mock_coordinator)
        mock_coordinator.fan_only_enabled = False
        await switch.async_turn_on()
        assert mock_coordinator.fan_only_enabled is True
