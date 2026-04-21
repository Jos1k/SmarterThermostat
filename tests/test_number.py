import pytest
from unittest.mock import MagicMock, AsyncMock

from custom_components.smarter_thermostat.const import (
    DEFAULT_CALIBRATION_WEIGHT,
    DEFAULT_OUTSIDE_TEMP_WEIGHT,
    DEFAULT_DEAD_BAND,
    DEFAULT_MIN_OFFSET_CHANGE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_MAX_OFFSET,
    DEFAULT_MIN_MODE_SWITCH_INTERVAL,
)
from custom_components.smarter_thermostat.number import (
    NUMBER_DEFINITIONS,
    SmarterThermostatNumber,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.entry_id = "test_entry_id"
    coordinator.config_entry.title = "Living Room AC"
    coordinator.calibration_weight = DEFAULT_CALIBRATION_WEIGHT
    coordinator.outside_temp_weight = DEFAULT_OUTSIDE_TEMP_WEIGHT
    coordinator.dead_band = DEFAULT_DEAD_BAND
    coordinator.min_offset_change = DEFAULT_MIN_OFFSET_CHANGE
    coordinator.update_interval_seconds = DEFAULT_UPDATE_INTERVAL
    coordinator.max_offset = DEFAULT_MAX_OFFSET
    coordinator.min_mode_switch_interval = DEFAULT_MIN_MODE_SWITCH_INTERVAL
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestNumberDefinitions:
    def test_all_params_have_definitions(self):
        keys = [d["key"] for d in NUMBER_DEFINITIONS]
        assert "calibration_weight" in keys
        assert "outside_temp_weight" in keys
        assert "dead_band" in keys
        assert "min_offset_change" in keys
        assert "update_interval" in keys
        assert "max_offset" in keys
        assert "min_mode_switch_interval" in keys

    def test_definitions_have_required_fields(self):
        for defn in NUMBER_DEFINITIONS:
            assert "key" in defn
            assert "name_suffix" in defn
            assert "min_value" in defn
            assert "max_value" in defn
            assert "step" in defn
            assert "coordinator_attr" in defn


class TestSmarterThermostatNumber:
    def test_calibration_weight_value(self, mock_coordinator):
        defn = next(d for d in NUMBER_DEFINITIONS if d["key"] == "calibration_weight")
        entity = SmarterThermostatNumber(mock_coordinator, defn)
        assert entity.native_value == DEFAULT_CALIBRATION_WEIGHT

    def test_unique_id(self, mock_coordinator):
        defn = next(d for d in NUMBER_DEFINITIONS if d["key"] == "calibration_weight")
        entity = SmarterThermostatNumber(mock_coordinator, defn)
        assert entity.unique_id == "test_entry_id_calibration_weight"

    @pytest.mark.asyncio
    async def test_set_value(self, mock_coordinator):
        defn = next(d for d in NUMBER_DEFINITIONS if d["key"] == "calibration_weight")
        entity = SmarterThermostatNumber(mock_coordinator, defn)
        await entity.async_set_native_value(0.5)
        assert mock_coordinator.calibration_weight == 0.5

    @pytest.mark.asyncio
    async def test_set_update_interval_triggers_coordinator_interval_change(self, mock_coordinator):
        defn = next(d for d in NUMBER_DEFINITIONS if d["key"] == "update_interval")
        entity = SmarterThermostatNumber(mock_coordinator, defn)
        await entity.async_set_native_value(120)
        assert mock_coordinator.update_interval_seconds == 120
