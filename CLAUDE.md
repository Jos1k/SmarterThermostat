# SmarterThermostat

Custom Home Assistant integration for AC units. Wraps a physical climate entity, uses external room + outside temperature sensors to calculate calibration offset, adjusts target temp sent to AC.

## Key Concepts

- **Offset-based calibration** — never turns AC on/off, adjusts target temp to compensate for sensor location discrepancy
- **Passthrough design** — mirrors presets, HVAC modes, fan modes, swing modes from source AC entity
- **Pure calibration module** — `calibration.py` has zero HA dependencies, pure math functions
- **Coordinator pattern** — `DataUpdateCoordinator` polls sensors on interval, standard HA approach

## Architecture

```
custom_components/smarter_thermostat/
├── __init__.py        # Setup, coordinator init
├── manifest.json      # HA integration manifest
├── config_flow.py     # UI config flow + options flow
├── const.py           # Constants, defaults, config keys
├── coordinator.py     # DataUpdateCoordinator
├── calibration.py     # Pure offset calculation (no HA imports)
├── climate.py         # Climate entity wrapping physical AC
├── number.py          # Number entities for tuning params
├── switch.py          # ON/OFF switch + fan-only toggle
├── strings.json       # Config flow UI strings
└── translations/en.json
```

## Design Spec

Full spec: `docs/superpowers/specs/2026-04-21-smarter-thermostat-design.md`

## Tech Stack

- Python 3.12+
- Home Assistant Core APIs
- No external dependencies beyond HA

## Commands

```bash
# Validate with HA (requires HA dev environment)
python -m pytest tests/
# Lint
ruff check custom_components/smarter_thermostat/
```

## Conventions

- Follow Home Assistant integration development guidelines
- Type hints on all public functions
- `calibration.py` must stay HA-independent (testable without HA)
- One integration entry = one AC unit
