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

    sys.modules['homeassistant.const'].UnitOfTemperature = UnitOfTemperature
    sys.modules['homeassistant.components.climate'].HVACMode = HVACMode
    sys.modules['homeassistant.components.climate'].HVACAction = HVACAction
    sys.modules['homeassistant.components.climate'].ClimateEntityFeature = ClimateEntityFeature
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
