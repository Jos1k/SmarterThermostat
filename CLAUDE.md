# SmarterThermostat

Custom Home Assistant integration for AC units. Wraps a physical climate entity, uses external room + outside temperature sensors to calculate calibration offset, adjusts target temp sent to AC.

## Key Concepts

- **Offset-based calibration** — never turns AC on/off, adjusts target temp to compensate for sensor location discrepancy
- **Passthrough design** — mirrors presets, HVAC modes, fan modes, swing modes from source AC entity
- **Dead-band fan-only** — switches to fan_only mode when room temp is within dead_band of target (cooling mode only), with compressor protection via min_mode_switch_interval
- **Pure calibration module** — `calibration.py` has zero HA dependencies, pure math functions
- **Coordinator pattern** — `DataUpdateCoordinator` polls sensors on interval, sends adjusted target and HVAC mode changes to AC via service calls

## Architecture

```
custom_components/smarter_thermostat/
├── __init__.py        # Setup, coordinator init, options change listener
├── manifest.json      # HA integration manifest
├── config_flow.py     # UI config flow + options flow
├── const.py           # Constants, defaults, config keys
├── coordinator.py     # DataUpdateCoordinator — offset calc, service calls, dead-band logic
├── calibration.py     # Pure offset calculation (no HA imports)
├── climate.py         # Climate entity wrapping physical AC (proxy + offset)
├── number.py          # Number entities for runtime tuning (7 params)
├── switch.py          # ON/OFF calibration switch + fan-only toggle
├── strings.json       # Config flow UI strings
└── translations/en.json
```

## Calibration Algorithm

```
sensor_offset = (room_temp - ac_temp) * calibration_weight
outside_factor = (outside_temp - 25.0) * outside_temp_weight * 0.1
total_offset = clamp(sensor_offset + outside_factor, -max_offset, max_offset)
adjusted_target = clamp(target_temp - total_offset, min_temp, max_temp)
```

## Entities Created Per Instance

- `climate.{name}` — virtual thermostat (proxy to physical AC)
- `switch.{name}_calibration` — enable/disable offset calibration
- `switch.{name}_fan_only` — enable/disable dead-band fan-only switching
- `number.{name}_calibration_weight` — 0.0–1.0 (default 0.8)
- `number.{name}_outside_temp_weight` — 0.0–1.0 (default 0.3)
- `number.{name}_dead_band` — 0.5–3.0°C (default 1.0)
- `number.{name}_min_offset_change` — 0.1–2.0 (default 0.5)
- `number.{name}_update_interval` — 10–300s (default 60)
- `number.{name}_max_offset` — 1.0–10.0 (default 5.0)
- `number.{name}_min_mode_switch_interval` — 60–600s (default 180)

## Design Spec

Full spec: `docs/superpowers/specs/2026-04-21-smarter-thermostat-design.md`

## Tech Stack

- Python 3.12+
- Home Assistant Core APIs
- No external dependencies beyond HA

## Commands

```bash
# Run tests (works without HA installed — conftest mocks HA modules)
python -m pytest tests/ -v
# Lint
ruff check custom_components/smarter_thermostat/
```

## Test Coverage

64 tests across 6 test files:
- `test_calibration.py` — offset calculation, adjusted target, clamping
- `test_coordinator.py` — init, update cycle, service calls, dead-band, unavailable handling
- `test_climate.py` — properties, proxy commands, extra attributes
- `test_number.py` — definitions, read/write, update_interval sync
- `test_switch.py` — calibration switch, fan-only switch
- `test_config_flow.py` — config flow, options flow

## Conventions

- Follow Home Assistant integration development guidelines
- Type hints on all public functions
- `calibration.py` must stay HA-independent (testable without HA)
- One integration entry = one AC unit
- Coordinator handles all service calls to physical AC (set_temperature, set_hvac_mode)
- Climate entity intercepts set_temperature (applies offset), proxies everything else
