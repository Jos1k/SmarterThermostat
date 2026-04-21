from unittest.mock import MagicMock
import sys

import pytest

# Mock homeassistant if not installed
if 'homeassistant' not in sys.modules:
    from unittest.mock import MagicMock

    # Create mock modules
    mock_ha = MagicMock()
    sys.modules['homeassistant'] = mock_ha
    sys.modules['homeassistant.const'] = MagicMock()
    sys.modules['homeassistant.components'] = MagicMock()
    sys.modules['homeassistant.components.climate'] = MagicMock()
    sys.modules['homeassistant.components.number'] = MagicMock()
    sys.modules['homeassistant.core'] = MagicMock()
    sys.modules['homeassistant.helpers'] = MagicMock()
    sys.modules['homeassistant.helpers.entity_platform'] = MagicMock()
    sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()
    sys.modules['homeassistant.data_entry_flow'] = MagicMock()

    # Mock voluptuous - make it functional
    class Schema:
        def __init__(self, schema_dict):
            self.schema = schema_dict

        def __call__(self, data):
            return data

    class Required:
        def __init__(self, key, default=None):
            self.key = key
            self.default = default

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other):
            if isinstance(other, Required):
                return self.key == other.key
            return False

    voluptuous_mock = MagicMock()
    voluptuous_mock.Schema = Schema
    voluptuous_mock.Required = Required
    sys.modules['voluptuous'] = voluptuous_mock

    # Mock selector
    class EntitySelectorConfig:
        def __init__(self, domain=None, device_class=None):
            self.domain = domain
            self.device_class = device_class

    class EntitySelector:
        def __init__(self, config):
            self.config = config

    class NumberSelectorConfig:
        def __init__(self, min=None, max=None, step=None, mode=None):
            self.min = min
            self.max = max
            self.step = step
            self.mode = mode

    class NumberSelector:
        def __init__(self, config):
            self.config = config

    selector_mock = MagicMock()
    selector_mock.EntitySelectorConfig = EntitySelectorConfig
    selector_mock.EntitySelector = EntitySelector
    selector_mock.NumberSelectorConfig = NumberSelectorConfig
    selector_mock.NumberSelector = NumberSelector
    sys.modules['homeassistant.helpers.selector'] = selector_mock

    # Define mock enums/classes
    class UnitOfTemperature:
        CELSIUS = "°C"

    class HVACMode:
        OFF = "off"
        COOL = "cool"
        HEAT = "heat"
        FAN_ONLY = "fan_only"
        AUTO = "auto"

    class HVACAction:
        COOLING = "cooling"

    class ClimateEntityFeature:
        TARGET_TEMPERATURE = 1
        FAN_MODE = 2
        SWING_MODE = 4
        PRESET_MODE = 8

    class ClimateEntity:
        _attr_has_entity_name = False
        _enable_turn_on_turn_off_backwards_compat = False

        @property
        def unique_id(self):
            return getattr(self, '_attr_unique_id', None)

        @property
        def name(self):
            return getattr(self, '_attr_name', None)

        @property
        def should_poll(self):
            return False

        async def async_write_ha_state(self):
            pass

        def async_on_remove(self, func):
            return func

    class NumberEntity:
        _attr_has_entity_name = False

        @property
        def unique_id(self):
            return self._attr_unique_id

        @property
        def name(self):
            return self._attr_name

        @property
        def native_value(self):
            raise NotImplementedError

        async def async_set_native_value(self, value):
            raise NotImplementedError

    class DataUpdateCoordinator:
        """Mock DataUpdateCoordinator."""
        def __init__(self, hass, logger, *, name, update_interval):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None

        async def async_refresh(self):
            pass

    class FlowResultType:
        """Mock FlowResultType."""
        FORM = "form"
        CREATE_ENTRY = "create_entry"
        ABORT = "abort"

    class ConfigFlow:
        """Mock ConfigFlow base class."""
        VERSION = 1

        def __init_subclass__(cls, domain=None, **kwargs):
            """Handle domain parameter in subclass definition."""
            super().__init_subclass__(**kwargs)
            if domain:
                cls.DOMAIN = domain

        def async_create_entry(self, *, title, data, **kwargs):
            return {
                "type": FlowResultType.CREATE_ENTRY,
                "title": title,
                "data": data,
            }

        def async_show_form(self, *, step_id, data_schema, errors=None, **kwargs):
            return {
                "type": FlowResultType.FORM,
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

    class OptionsFlow:
        """Mock OptionsFlow base class."""

        def async_create_entry(self, *, title, data, **kwargs):
            return {
                "type": FlowResultType.CREATE_ENTRY,
                "title": title,
                "data": data,
            }

        def async_show_form(self, *, step_id, data_schema, errors=None, **kwargs):
            return {
                "type": FlowResultType.FORM,
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

    # Define constants
    ATTR_ENTITY_ID = "entity_id"
    ATTR_TEMPERATURE = "temperature"

    sys.modules['homeassistant.const'].UnitOfTemperature = UnitOfTemperature
    # Define types
    class HomeAssistant:
        """Mock HomeAssistant."""
        pass

    class AddEntitiesCallback:
        """Mock AddEntitiesCallback."""
        pass

    sys.modules['homeassistant.const'].ATTR_ENTITY_ID = ATTR_ENTITY_ID
    sys.modules['homeassistant.const'].ATTR_TEMPERATURE = ATTR_TEMPERATURE
    sys.modules['homeassistant.components.climate'].HVACMode = HVACMode
    sys.modules['homeassistant.components.climate'].HVACAction = HVACAction
    sys.modules['homeassistant.components.climate'].ClimateEntityFeature = ClimateEntityFeature
    sys.modules['homeassistant.components.climate'].ClimateEntity = ClimateEntity
    sys.modules['homeassistant.components.number'].NumberEntity = NumberEntity
    sys.modules['homeassistant.helpers.update_coordinator'].DataUpdateCoordinator = DataUpdateCoordinator
    sys.modules['homeassistant.core'].HomeAssistant = HomeAssistant
    sys.modules['homeassistant.helpers.entity_platform'].AddEntitiesCallback = AddEntitiesCallback
    sys.modules['homeassistant.data_entry_flow'].FlowResultType = FlowResultType

    # Create a module-like object for config_entries
    class ConfigEntry:
        """Mock ConfigEntry."""
        pass

    class ConfigEntriesModule:
        ConfigFlow = ConfigFlow
        OptionsFlow = OptionsFlow
        ConfigEntry = ConfigEntry

    config_entries_module = ConfigEntriesModule()
    sys.modules['homeassistant.config_entries'] = config_entries_module
    # Also set it as attribute on the main mock so imports work
    mock_ha.config_entries = config_entries_module
else:
    from homeassistant.const import UnitOfTemperature
    from homeassistant.components.climate import (
        HVACMode,
        HVACAction,
        ClimateEntityFeature,
    )


@pytest.fixture
def mock_ac_state():
    state = MagicMock()
    state.entity_id = "climate.test_ac"
    state.state = HVACMode.COOL
    state.attributes = {
        "hvac_modes": [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.AUTO],
        "preset_modes": ["none", "eco", "sleep", "boost"],
        "fan_modes": ["auto", "low", "medium", "high"],
        "swing_modes": ["off", "vertical", "horizontal", "both"],
        "min_temp": 16.0,
        "max_temp": 30.0,
        "current_temperature": 24.0,
        "temperature": 22.0,
        "hvac_action": HVACAction.COOLING,
        "fan_mode": "auto",
        "swing_mode": "off",
        "preset_mode": "none",
        "supported_features": (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE
            | ClimateEntityFeature.PRESET_MODE
        ),
    }
    return state


@pytest.fixture
def mock_room_sensor_state():
    state = MagicMock()
    state.entity_id = "sensor.room_temperature"
    state.state = "26.0"
    state.attributes = {
        "device_class": "temperature",
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
    }
    return state


@pytest.fixture
def mock_outside_sensor_state():
    state = MagicMock()
    state.entity_id = "sensor.outside_temperature"
    state.state = "35.0"
    state.attributes = {
        "device_class": "temperature",
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
    }
    return state
