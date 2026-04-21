# SmarterThermostat Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Home Assistant custom integration that wraps a physical AC climate entity, calibrates its target temperature using external room and outside sensors, and exposes runtime-tunable parameters as HA entities.

**Architecture:** Modular — coordinator fetches sensor data on interval, passes to pure calibration module, climate entity applies offset to AC commands. Number/switch entities expose tuning params. Config flow for setup, options flow for tuning.

**Tech Stack:** Python 3.12+, Home Assistant Core APIs, pytest for testing

**Design Spec:** `docs/superpowers/specs/2026-04-21-smarter-thermostat-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `custom_components/smarter_thermostat/__init__.py` | Integration setup, coordinator creation, platform forwarding |
| `custom_components/smarter_thermostat/manifest.json` | HA integration metadata |
| `custom_components/smarter_thermostat/const.py` | All constants, config keys, defaults, domain name |
| `custom_components/smarter_thermostat/calibration.py` | Pure offset calculation — no HA imports |
| `custom_components/smarter_thermostat/coordinator.py` | DataUpdateCoordinator — polls sensors, runs calibration, dead-band logic |
| `custom_components/smarter_thermostat/climate.py` | Climate entity — wraps AC, proxies commands, applies offset |
| `custom_components/smarter_thermostat/number.py` | Number entities for tuning parameters |
| `custom_components/smarter_thermostat/switch.py` | ON/OFF switch + fan-only mode switch |
| `custom_components/smarter_thermostat/config_flow.py` | UI config flow + options flow |
| `custom_components/smarter_thermostat/strings.json` | Config flow UI strings |
| `custom_components/smarter_thermostat/translations/en.json` | English translations |
| `tests/conftest.py` | Shared pytest fixtures (mock HA, mock entities) |
| `tests/test_calibration.py` | Unit tests for pure calibration math |
| `tests/test_coordinator.py` | Tests for coordinator update cycle |
| `tests/test_climate.py` | Tests for climate entity behavior |
| `tests/test_number.py` | Tests for number entities |
| `tests/test_switch.py` | Tests for switch entities |
| `tests/test_config_flow.py` | Tests for config and options flows |
| `pyproject.toml` | Project config, test dependencies |

---

## Task 1: Project Scaffolding & Constants

**Files:**
- Create: `custom_components/smarter_thermostat/manifest.json`
- Create: `custom_components/smarter_thermostat/const.py`
- Create: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `custom_components/__init__.py`
- Create: `custom_components/smarter_thermostat/__init__.py` (empty, placeholder)

- [ ] **Step 1: Create manifest.json**

```json
{
  "domain": "smarter_thermostat",
  "name": "Smarter Thermostat",
  "codeowners": [],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/ihor-hadzera/SmarterThermostat",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/ihor-hadzera/SmarterThermostat/issues",
  "version": "0.1.0"
}
```

- [ ] **Step 2: Create const.py with all constants and defaults**

```python
from typing import Final

DOMAIN: Final = "smarter_thermostat"

CONF_SOURCE_CLIMATE: Final = "source_climate"
CONF_ROOM_SENSOR: Final = "room_sensor"
CONF_OUTSIDE_SENSOR: Final = "outside_sensor"

CONF_CALIBRATION_WEIGHT: Final = "calibration_weight"
CONF_OUTSIDE_TEMP_WEIGHT: Final = "outside_temp_weight"
CONF_DEAD_BAND: Final = "dead_band"
CONF_MIN_OFFSET_CHANGE: Final = "min_offset_change"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_MAX_OFFSET: Final = "max_offset"
CONF_MIN_MODE_SWITCH_INTERVAL: Final = "min_mode_switch_interval"
CONF_FAN_ONLY_ENABLED: Final = "fan_only_enabled"

DEFAULT_CALIBRATION_WEIGHT: Final = 0.8
DEFAULT_OUTSIDE_TEMP_WEIGHT: Final = 0.3
DEFAULT_DEAD_BAND: Final = 1.0
DEFAULT_MIN_OFFSET_CHANGE: Final = 0.5
DEFAULT_UPDATE_INTERVAL: Final = 60
DEFAULT_MAX_OFFSET: Final = 5.0
DEFAULT_MIN_MODE_SWITCH_INTERVAL: Final = 180
DEFAULT_FAN_ONLY_ENABLED: Final = True

OUTSIDE_TEMP_REFERENCE: Final = 25.0
OUTSIDE_TEMP_SCALE: Final = 0.1

PLATFORMS: Final = ["climate", "number", "switch"]
```

- [ ] **Step 3: Create pyproject.toml**

```toml
[project]
name = "smarter-thermostat"
version = "0.1.0"
description = "Home Assistant integration for smart AC thermostat calibration"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py312"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-homeassistant-custom-component>=0.13",
    "ruff>=0.4",
]
```

- [ ] **Step 4: Create test scaffolding**

Create `tests/__init__.py` (empty file).

Create `tests/conftest.py`:

```python
from unittest.mock import MagicMock

import pytest
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
```

Create `custom_components/__init__.py` (empty file).
Create `custom_components/smarter_thermostat/__init__.py` (empty file, will be filled in Task 6).

- [ ] **Step 5: Commit**

```bash
git add custom_components/ tests/ pyproject.toml
git commit -m "feat: scaffold project with manifest, constants, and test fixtures"
```

---

## Task 2: Calibration Module (Pure Math, TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/calibration.py`
- Create: `tests/test_calibration.py`

- [ ] **Step 1: Write failing tests for calculate_offset**

Create `tests/test_calibration.py`:

```python
import pytest

from custom_components.smarter_thermostat.calibration import calculate_offset


class TestCalculateOffset:
    def test_no_discrepancy_no_outside_effect(self):
        offset = calculate_offset(
            room_temp=24.0,
            ac_temp=24.0,
            outside_temp=25.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        assert offset == 0.0

    def test_room_warmer_than_ac(self):
        offset = calculate_offset(
            room_temp=26.0,
            ac_temp=24.0,
            outside_temp=25.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        assert offset == pytest.approx(1.6)

    def test_room_cooler_than_ac(self):
        offset = calculate_offset(
            room_temp=22.0,
            ac_temp=24.0,
            outside_temp=25.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        assert offset == pytest.approx(-1.6)

    def test_hot_outside_adds_positive_factor(self):
        offset = calculate_offset(
            room_temp=24.0,
            ac_temp=24.0,
            outside_temp=40.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        expected = (40.0 - 25.0) * 0.3 * 0.1
        assert offset == pytest.approx(expected)

    def test_cold_outside_adds_negative_factor(self):
        offset = calculate_offset(
            room_temp=24.0,
            ac_temp=24.0,
            outside_temp=10.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        expected = (10.0 - 25.0) * 0.3 * 0.1
        assert offset == pytest.approx(expected)

    def test_combined_sensor_and_outside(self):
        offset = calculate_offset(
            room_temp=26.0,
            ac_temp=24.0,
            outside_temp=40.0,
            calibration_weight=0.8,
            outside_temp_weight=0.3,
            max_offset=5.0,
        )
        sensor_offset = (26.0 - 24.0) * 0.8
        outside_factor = (40.0 - 25.0) * 0.3 * 0.1
        expected = sensor_offset + outside_factor
        assert offset == pytest.approx(expected)

    def test_clamp_to_max_offset(self):
        offset = calculate_offset(
            room_temp=35.0,
            ac_temp=24.0,
            outside_temp=45.0,
            calibration_weight=1.0,
            outside_temp_weight=1.0,
            max_offset=5.0,
        )
        assert offset == 5.0

    def test_clamp_to_negative_max_offset(self):
        offset = calculate_offset(
            room_temp=15.0,
            ac_temp=30.0,
            outside_temp=0.0,
            calibration_weight=1.0,
            outside_temp_weight=1.0,
            max_offset=5.0,
        )
        assert offset == -5.0

    def test_zero_weights(self):
        offset = calculate_offset(
            room_temp=30.0,
            ac_temp=20.0,
            outside_temp=40.0,
            calibration_weight=0.0,
            outside_temp_weight=0.0,
            max_offset=5.0,
        )
        assert offset == 0.0


class TestCalculateAdjustedTarget:
    def test_basic_adjustment(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target

        adjusted = calculate_adjusted_target(
            target_temp=24.0,
            offset=2.0,
            min_temp=16.0,
            max_temp=30.0,
        )
        assert adjusted == 22.0

    def test_clamp_to_min(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target

        adjusted = calculate_adjusted_target(
            target_temp=17.0,
            offset=3.0,
            min_temp=16.0,
            max_temp=30.0,
        )
        assert adjusted == 16.0

    def test_clamp_to_max(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target

        adjusted = calculate_adjusted_target(
            target_temp=29.0,
            offset=-3.0,
            min_temp=16.0,
            max_temp=30.0,
        )
        assert adjusted == 30.0

    def test_zero_offset(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target

        adjusted = calculate_adjusted_target(
            target_temp=24.0,
            offset=0.0,
            min_temp=16.0,
            max_temp=30.0,
        )
        assert adjusted == 24.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_calibration.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'custom_components.smarter_thermostat.calibration'`

- [ ] **Step 3: Implement calibration.py**

Create `custom_components/smarter_thermostat/calibration.py`:

```python
from custom_components.smarter_thermostat.const import OUTSIDE_TEMP_REFERENCE, OUTSIDE_TEMP_SCALE


def calculate_offset(
    room_temp: float,
    ac_temp: float,
    outside_temp: float,
    calibration_weight: float,
    outside_temp_weight: float,
    max_offset: float,
) -> float:
    sensor_offset = (room_temp - ac_temp) * calibration_weight
    outside_factor = (outside_temp - OUTSIDE_TEMP_REFERENCE) * outside_temp_weight * OUTSIDE_TEMP_SCALE
    total_offset = sensor_offset + outside_factor
    return max(-max_offset, min(max_offset, total_offset))


def calculate_adjusted_target(
    target_temp: float,
    offset: float,
    min_temp: float,
    max_temp: float,
) -> float:
    adjusted = target_temp - offset
    return max(min_temp, min(max_temp, adjusted))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_calibration.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/smarter_thermostat/calibration.py tests/test_calibration.py
git commit -m "feat: add calibration module with offset and adjusted target calculation"
```

---

## Task 3: Switch Entities (TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/switch.py`
- Create: `tests/test_switch.py`

- [ ] **Step 1: Write failing tests for switch entities**

Create `tests/test_switch.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_switch.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement switch.py**

Create `custom_components/smarter_thermostat/switch.py`:

```python
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
    def is_on(self) -> bool:
        return self._coordinator.fan_only_enabled

    async def async_turn_on(self, **kwargs) -> None:
        self._coordinator.fan_only_enabled = True

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.fan_only_enabled = False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_switch.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/smarter_thermostat/switch.py tests/test_switch.py
git commit -m "feat: add ON/OFF and fan-only switch entities"
```

---

## Task 4: Number Entities (TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/number.py`
- Create: `tests/test_number.py`

- [ ] **Step 1: Write failing tests for number entities**

Create `tests/test_number.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_number.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement number.py**

Create `custom_components/smarter_thermostat/number.py`:

```python
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DEFAULT_CALIBRATION_WEIGHT,
    DEFAULT_OUTSIDE_TEMP_WEIGHT,
    DEFAULT_DEAD_BAND,
    DEFAULT_MIN_OFFSET_CHANGE,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_MAX_OFFSET,
    DEFAULT_MIN_MODE_SWITCH_INTERVAL,
)

NUMBER_DEFINITIONS: list[dict] = [
    {
        "key": "calibration_weight",
        "name_suffix": "Calibration Weight",
        "min_value": 0.0,
        "max_value": 1.0,
        "step": 0.05,
        "coordinator_attr": "calibration_weight",
    },
    {
        "key": "outside_temp_weight",
        "name_suffix": "Outside Temp Weight",
        "min_value": 0.0,
        "max_value": 1.0,
        "step": 0.05,
        "coordinator_attr": "outside_temp_weight",
    },
    {
        "key": "dead_band",
        "name_suffix": "Dead Band",
        "min_value": 0.5,
        "max_value": 3.0,
        "step": 0.1,
        "coordinator_attr": "dead_band",
    },
    {
        "key": "min_offset_change",
        "name_suffix": "Min Offset Change",
        "min_value": 0.1,
        "max_value": 2.0,
        "step": 0.1,
        "coordinator_attr": "min_offset_change",
    },
    {
        "key": "update_interval",
        "name_suffix": "Update Interval",
        "min_value": 10,
        "max_value": 300,
        "step": 5,
        "coordinator_attr": "update_interval_seconds",
    },
    {
        "key": "max_offset",
        "name_suffix": "Max Offset",
        "min_value": 1.0,
        "max_value": 10.0,
        "step": 0.5,
        "coordinator_attr": "max_offset",
    },
    {
        "key": "min_mode_switch_interval",
        "name_suffix": "Min Mode Switch Interval",
        "min_value": 60,
        "max_value": 600,
        "step": 10,
        "coordinator_attr": "min_mode_switch_interval",
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SmarterThermostatNumber(coordinator, defn)
        for defn in NUMBER_DEFINITIONS
    ])


class SmarterThermostatNumber(NumberEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, definition: dict) -> None:
        self._coordinator = coordinator
        self._definition = definition
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{definition['key']}"
        self._attr_name = f"{coordinator.config_entry.title} {definition['name_suffix']}"
        self._attr_native_min_value = definition["min_value"]
        self._attr_native_max_value = definition["max_value"]
        self._attr_native_step = definition["step"]

    @property
    def native_value(self) -> float:
        return getattr(self._coordinator, self._definition["coordinator_attr"])

    async def async_set_native_value(self, value: float) -> None:
        setattr(self._coordinator, self._definition["coordinator_attr"], value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_number.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/smarter_thermostat/number.py tests/test_number.py
git commit -m "feat: add number entities for tuning parameters"
```

---

## Task 5: Coordinator (TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/coordinator.py`
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write failing tests for coordinator**

Create `tests/test_coordinator.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import timedelta

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


def make_state(entity_id: str, state: str, attributes: dict | None = None):
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement coordinator.py**

Create `custom_components/smarter_thermostat/coordinator.py`:

```python
import logging
import time
from datetime import timedelta

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

        self.target_temp: float | None = None
        self._last_offset: float = 0.0
        self._last_mode_switch_time: float = 0.0
        self._previous_hvac_mode: str | None = None
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

    def _evaluate_deadband(self, room_temp: float, current_hvac_mode: str) -> str | None:
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
        suggested_hvac_mode: str | None,
        adjusted_target: float | None = None,
        room_temp: float | None = None,
        ac_temp: float | None = None,
        outside_temp: float | None = None,
    ) -> dict:
        return {
            "offset": offset,
            "adjusted_target": adjusted_target,
            "suggested_hvac_mode": suggested_hvac_mode,
            "room_temp": room_temp,
            "ac_temp": ac_temp,
            "outside_temp": outside_temp,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_coordinator.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/smarter_thermostat/coordinator.py tests/test_coordinator.py
git commit -m "feat: add coordinator with calibration, dead-band, and compressor protection"
```

---

## Task 6: Climate Entity (TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/climate.py`
- Create: `tests/test_climate.py`

- [ ] **Step 1: Write failing tests for climate entity**

Create `tests/test_climate.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_climate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement climate.py**

Create `custom_components/smarter_thermostat/climate.py`:

```python
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_SOURCE_CLIMATE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SmarterThermostatClimate(coordinator)])


class SmarterThermostatClimate(ClimateEntity):
    _attr_has_entity_name = False
    _enable_turn_on_turn_off_backwards_compat = False

    def __init__(self, coordinator) -> None:
        self._coordinator = coordinator
        self._source_entity_id = coordinator.config_entry.data[CONF_SOURCE_CLIMATE]
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_climate"
        self._attr_name = coordinator.config_entry.title

    @property
    def _ac_state(self):
        return self._coordinator.hass.states.get(self._source_entity_id)

    @property
    def supported_features(self) -> ClimateEntityFeature:
        ac = self._ac_state
        if ac is None:
            return ClimateEntityFeature(0)
        return ClimateEntityFeature(ac.attributes.get("supported_features", 0))

    @property
    def hvac_modes(self) -> list[HVACMode]:
        ac = self._ac_state
        if ac is None:
            return []
        return ac.attributes.get("hvac_modes", [])

    @property
    def hvac_mode(self) -> HVACMode | None:
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
    def current_temperature(self) -> float | None:
        if not self._coordinator.enabled:
            ac = self._ac_state
            return ac.attributes.get("current_temperature") if ac else None
        data = self._coordinator.data
        if data and data.get("room_temp") is not None:
            return data["room_temp"]
        ac = self._ac_state
        return ac.attributes.get("current_temperature") if ac else None

    @property
    def target_temperature(self) -> float | None:
        return self._coordinator.target_temp

    @property
    def min_temp(self) -> float:
        ac = self._ac_state
        return ac.attributes.get("min_temp", 16.0) if ac else 16.0

    @property
    def max_temp(self) -> float:
        ac = self._ac_state
        return ac.attributes.get("max_temp", 30.0) if ac else 30.0

    @property
    def preset_modes(self) -> list[str] | None:
        ac = self._ac_state
        return ac.attributes.get("preset_modes") if ac else None

    @property
    def preset_mode(self) -> str | None:
        ac = self._ac_state
        return ac.attributes.get("preset_mode") if ac else None

    @property
    def fan_modes(self) -> list[str] | None:
        ac = self._ac_state
        return ac.attributes.get("fan_modes") if ac else None

    @property
    def fan_mode(self) -> str | None:
        ac = self._ac_state
        return ac.attributes.get("fan_mode") if ac else None

    @property
    def swing_modes(self) -> list[str] | None:
        ac = self._ac_state
        return ac.attributes.get("swing_modes") if ac else None

    @property
    def swing_mode(self) -> str | None:
        ac = self._ac_state
        return ac.attributes.get("swing_mode") if ac else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self._coordinator.data or {}
        return {
            "calibration_offset": data.get("offset", 0.0),
            "adjusted_target": data.get("adjusted_target"),
            "ac_temperature": data.get("ac_temp"),
            "outside_temperature": data.get("outside_temp"),
        }

    async def _async_call_ac_service(self, service: str, **kwargs) -> None:
        kwargs[ATTR_ENTITY_ID] = self._source_entity_id
        await self._coordinator.hass.services.async_call("climate", service, kwargs)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._coordinator.target_temp = temp
            data = self._coordinator.data or {}
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

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_climate.py -v`
Expected: All 17 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/smarter_thermostat/climate.py tests/test_climate.py
git commit -m "feat: add climate entity with proxy and offset logic"
```

---

## Task 7: Config Flow & Options Flow (TDD)

**Files:**
- Create: `custom_components/smarter_thermostat/config_flow.py`
- Create: `custom_components/smarter_thermostat/strings.json`
- Create: `custom_components/smarter_thermostat/translations/en.json`
- Create: `tests/test_config_flow.py`

- [ ] **Step 1: Write failing tests for config flow**

Create `tests/test_config_flow.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config_flow.py**

Create `custom_components/smarter_thermostat/config_flow.py`:

```python
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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

USER_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required(CONF_SOURCE_CLIMATE): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="climate"),
    ),
    vol.Required(CONF_ROOM_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature"),
    ),
    vol.Required(CONF_OUTSIDE_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature"),
    ),
})


def options_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required(
            CONF_CALIBRATION_WEIGHT,
            default=options.get(CONF_CALIBRATION_WEIGHT, DEFAULT_CALIBRATION_WEIGHT),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.0, max=1.0, step=0.05, mode="slider",
        )),
        vol.Required(
            CONF_OUTSIDE_TEMP_WEIGHT,
            default=options.get(CONF_OUTSIDE_TEMP_WEIGHT, DEFAULT_OUTSIDE_TEMP_WEIGHT),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.0, max=1.0, step=0.05, mode="slider",
        )),
        vol.Required(
            CONF_DEAD_BAND,
            default=options.get(CONF_DEAD_BAND, DEFAULT_DEAD_BAND),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.5, max=3.0, step=0.1, mode="slider",
        )),
        vol.Required(
            CONF_MIN_OFFSET_CHANGE,
            default=options.get(CONF_MIN_OFFSET_CHANGE, DEFAULT_MIN_OFFSET_CHANGE),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=0.1, max=2.0, step=0.1, mode="slider",
        )),
        vol.Required(
            CONF_UPDATE_INTERVAL,
            default=options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=10, max=300, step=5, mode="slider",
        )),
        vol.Required(
            CONF_MAX_OFFSET,
            default=options.get(CONF_MAX_OFFSET, DEFAULT_MAX_OFFSET),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=1.0, max=10.0, step=0.5, mode="slider",
        )),
        vol.Required(
            CONF_MIN_MODE_SWITCH_INTERVAL,
            default=options.get(CONF_MIN_MODE_SWITCH_INTERVAL, DEFAULT_MIN_MODE_SWITCH_INTERVAL),
        ): selector.NumberSelector(selector.NumberSelectorConfig(
            min=60, max=600, step=10, mode="slider",
        )),
        vol.Required(
            CONF_FAN_ONLY_ENABLED,
            default=options.get(CONF_FAN_ONLY_ENABLED, DEFAULT_FAN_ONLY_ENABLED),
        ): bool,
    })


class SmarterThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    CONF_SOURCE_CLIMATE: user_input[CONF_SOURCE_CLIMATE],
                    CONF_ROOM_SENSOR: user_input[CONF_ROOM_SENSOR],
                    CONF_OUTSIDE_SENSOR: user_input[CONF_OUTSIDE_SENSOR],
                },
            )
        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmarterThermostatOptionsFlow(config_entry)


class SmarterThermostatOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(self._config_entry.options),
        )
```

- [ ] **Step 4: Create strings.json**

Create `custom_components/smarter_thermostat/strings.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up Smarter Thermostat",
        "data": {
          "name": "Name",
          "source_climate": "Source AC climate entity",
          "room_sensor": "Room temperature sensor",
          "outside_sensor": "Outside temperature sensor"
        }
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Smarter Thermostat Options",
        "data": {
          "calibration_weight": "Calibration weight (0.0–1.0)",
          "outside_temp_weight": "Outside temp weight (0.0–1.0)",
          "dead_band": "Dead band (°C)",
          "min_offset_change": "Min offset change (°C)",
          "update_interval": "Update interval (seconds)",
          "max_offset": "Max offset (°C)",
          "min_mode_switch_interval": "Min mode switch interval (seconds)",
          "fan_only_enabled": "Enable fan-only in dead band"
        }
      }
    }
  }
}
```

- [ ] **Step 5: Create translations/en.json**

```bash
mkdir -p custom_components/smarter_thermostat/translations
```

Create `custom_components/smarter_thermostat/translations/en.json` with identical content to `strings.json` above.

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: All 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add custom_components/smarter_thermostat/config_flow.py custom_components/smarter_thermostat/strings.json custom_components/smarter_thermostat/translations/ tests/test_config_flow.py
git commit -m "feat: add config flow and options flow with UI strings"
```

---

## Task 8: Integration Setup (__init__.py)

**Files:**
- Modify: `custom_components/smarter_thermostat/__init__.py`

- [ ] **Step 1: Implement __init__.py**

Write `custom_components/smarter_thermostat/__init__.py`:

```python
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import SmarterThermostatCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SmarterThermostatCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 2: Verify all tests still pass**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add custom_components/smarter_thermostat/__init__.py
git commit -m "feat: add integration setup with coordinator init and platform forwarding"
```

---

## Task 9: Full Integration Test

**Files:**
- No new files — run all existing tests together

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run ruff lint**

Run: `ruff check custom_components/smarter_thermostat/`
Expected: No errors

- [ ] **Step 3: Fix any issues found in steps 1-2**

If any tests fail or lint errors found, fix them.

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve any test or lint issues from integration test"
```

(Skip this step if no fixes needed.)

---

## Task 10: Final Review & Documentation

**Files:**
- Modify: `CLAUDE.md` (update if any architecture changed)
- Verify: `custom_components/smarter_thermostat/manifest.json`

- [ ] **Step 1: Verify manifest.json has correct version and metadata**

Read `custom_components/smarter_thermostat/manifest.json` and confirm all fields are correct.

- [ ] **Step 2: Verify all files exist**

Run: `find custom_components/smarter_thermostat -type f | sort`

Expected output:
```
custom_components/smarter_thermostat/__init__.py
custom_components/smarter_thermostat/calibration.py
custom_components/smarter_thermostat/climate.py
custom_components/smarter_thermostat/config_flow.py
custom_components/smarter_thermostat/const.py
custom_components/smarter_thermostat/coordinator.py
custom_components/smarter_thermostat/manifest.json
custom_components/smarter_thermostat/number.py
custom_components/smarter_thermostat/strings.json
custom_components/smarter_thermostat/switch.py
custom_components/smarter_thermostat/translations/en.json
```

- [ ] **Step 3: Run full test suite one final time**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: final review and verification"
```

(Skip if no changes needed.)
