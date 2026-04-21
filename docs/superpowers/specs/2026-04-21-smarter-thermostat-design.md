# SmarterThermostat — Design Spec

Custom Home Assistant integration that wraps a physical AC climate entity, uses external room and outside temperature sensors to calculate a calibration offset, and adjusts the target temperature sent to the AC accordingly.

## Goals

- Simple, focused integration for AC units only (no boilers, valves, or radiators)
- Offset-based calibration — never fights AC's internal thermostat loop
- Reuse presets, HVAC modes, fan modes, and swing modes from source AC entity
- Runtime-tunable parameters exposed as HA entities
- ON/OFF switch for enabling/disabling calibration (passthrough when off)
- Per-instance design — one integration entry per AC, HA handles cross-room orchestration

## Architecture: Modular (Approach B)

```
custom_components/smarter_thermostat/
├── __init__.py              # Integration setup, coordinator init
├── manifest.json            # HA integration manifest
├── config_flow.py           # UI config flow + options flow
├── const.py                 # Constants, defaults, config keys
├── coordinator.py           # DataUpdateCoordinator — polls sensors, triggers recalc
├── calibration.py           # Pure math — offset calculation, no HA deps
├── climate.py               # Climate entity — wraps physical AC
├── number.py                # Number entities for tuning params
├── switch.py                # ON/OFF switch entity + fan-only toggle
├── strings.json             # UI strings for config flow
└── translations/
    └── en.json              # English translations
```

### Data Flow

```
Coordinator (every update_interval seconds)
  → reads room_temp, ac_temp, outside_temp from HA states
  → passes to calibration.calculate_offset()
  → applies min_offset_change guard
  → handles dead-band / fan-only logic
  → stores result
  → climate entity reads offset, adjusts target sent to AC
```

## Entities

| Entity | Platform | Purpose |
|---|---|---|
| `climate.smarter_thermostat_<name>` | climate | Main thermostat — mirrors HVAC modes, presets, fan, swing from AC |
| `switch.smarter_thermostat_<name>` | switch | ON = active calibration, OFF = passthrough |
| `number.smarter_thermostat_<name>_calibration_weight` | number | Runtime tunable (0.0–1.0, default 0.8) |
| `number.smarter_thermostat_<name>_outside_temp_weight` | number | Runtime tunable (0.0–1.0, default 0.3) |
| `number.smarter_thermostat_<name>_dead_band` | number | Runtime tunable (0.5–3.0 °C, default 1.0) |
| `number.smarter_thermostat_<name>_min_offset_change` | number | Runtime tunable (0.1–2.0 °C, default 0.5) |
| `number.smarter_thermostat_<name>_update_interval` | number | Runtime tunable (10–300 seconds, default 60) |
| `number.smarter_thermostat_<name>_max_offset` | number | Runtime tunable (1.0–10.0 °C, default 5.0) |
| `number.smarter_thermostat_<name>_min_mode_switch_interval` | number | Runtime tunable (60–600 seconds, default 180) |
| `switch.smarter_thermostat_<name>_fan_only_mode` | switch | Enable/disable fan-only in dead-band |

## Calibration Algorithm

Pure functions in `calibration.py`, no HA dependencies.

### Offset Calculation

```python
def calculate_offset(
    room_temp: float,
    ac_temp: float,
    outside_temp: float,
    calibration_weight: float,
    outside_temp_weight: float,
    max_offset: float,
) -> float:
```

**Step 1 — Sensor discrepancy:**
```
sensor_offset = (room_temp - ac_temp) * calibration_weight
```

**Step 2 — Outside temperature compensation:**
```
outside_factor = (outside_temp - 25.0) * outside_temp_weight * 0.1
```
Reference point 25°C. Hot outside → positive factor (need more cooling). Cold outside → negative.

**Step 3 — Total offset with safety clamp:**
```
total_offset = clamp(sensor_offset + outside_factor, -max_offset, max_offset)
```

**Step 4 — Adjusted target:**
```
adjusted_target = target_temp - total_offset
```
Clamped to AC's min_temp / max_temp range.

Offset direction works correctly for both cooling and heating without sign flip.

## Dead-Band & Fan-Only Logic

When `room_temp` is within `target ± dead_band`:
- **Cooling mode:** switch to fan_only (distributes air, prevents short-cycling)
- **Heating mode:** do NOT switch to fan_only (blowing unheated air makes it worse) — just let AC idle naturally

When `room_temp` drifts outside dead_band and AC is in fan_only due to dead-band:
- Restore previous HVAC mode (cool/heat/auto)

Fan-only dead-band behavior controlled by `fan_only_mode` switch entity. When disabled, dead-band has no effect on HVAC mode.

## Compressor Protection

`min_mode_switch_interval` (default 180 seconds) prevents rapid toggling between fan_only and cooling/heating modes. If last mode switch was less than this interval ago, skip the switch. Protects compressor on ACs without built-in delay.

## Climate Entity Behavior

### Proxied from Source AC (passthrough)

- `hvac_modes` — full list from AC
- `preset_modes` — full list from AC
- `fan_modes` — full list from AC
- `swing_modes` — full list from AC
- `min_temp` / `max_temp` — from AC
- `temperature_unit` — from AC

### Proxied Commands (sent directly to AC)

- `set_fan_mode()`
- `set_swing_mode()`
- `set_preset_mode()`
- `set_hvac_mode()`

### Intercepted Commands

- `set_temperature()` — stores user's desired target, coordinator applies offset before sending to AC

### State Reporting

- `current_temperature` → from room sensor (not AC's built-in)
- `target_temperature` → user's desired target (not adjusted value)
- `hvac_mode` → current mode from AC
- `hvac_action` → current action from AC (cooling, idle, fan)

### Extra State Attributes (debugging/transparency)

- `calibration_offset` — current calculated offset
- `adjusted_target` — what's actually sent to AC
- `ac_temperature` — AC's built-in sensor reading
- `outside_temperature` — outside sensor reading

### Switch OFF Behavior (passthrough mode)

- Climate entity still works, offset = 0
- `current_temperature` switches back to AC's built-in sensor
- All commands pass through unmodified
- Transparent proxy — AC works as if integration doesn't exist

## Config Flow

### Initial Setup (one step)

| Field | Type | Required |
|---|---|---|
| Name | string | yes |
| Source climate entity | entity picker (climate.*) | yes |
| Room temperature sensor | entity picker (sensor.*, device_class=temperature) | yes |
| Outside temperature sensor | entity picker (sensor.*, device_class=temperature) | yes |

### Options Flow (Configure button)

All tuning parameters adjustable post-setup:

| Field | Type | Range | Default |
|---|---|---|---|
| Calibration weight | float | 0.0–1.0 | 0.8 |
| Outside temp weight | float | 0.0–1.0 | 0.3 |
| Dead band | float | 0.5–3.0 °C | 1.0 |
| Min offset change | float | 0.1–2.0 °C | 0.5 |
| Update interval | int | 10–300 seconds | 60 |
| Max offset | float | 1.0–10.0 °C | 5.0 |
| Min mode switch interval | int | 60–600 seconds | 180 |
| Fan-only in dead-band | bool | — | true |

Options flow values serve as initial values for number/switch entities. Runtime changes via entities take precedence. Options flow resets them.

### Validation

- Source climate entity must exist and be available
- Both sensors must have `device_class: temperature`
- No self-referencing (cannot pick integration's own climate entity as source)

## Coordinator & Update Cycle

### Update Cycle

```
every update_interval:
  1. Read room_temp, ac_temp, outside_temp from HA states
  2. If any sensor unavailable → log warning, keep last known offset, skip
  3. If switch OFF → offset = 0, skip calibration
  4. Calculate new_offset via calibration module
  5. If abs(new_offset - last_offset) < min_offset_change → skip
  6. Store new offset
  7. Dead-band check (only if fan_only_mode enabled):
     - Cooling + room_temp within target ± dead_band → set fan_only (respect min_mode_switch_interval)
     - Outside dead_band AND currently in fan_only from dead_band → restore previous mode (respect min_mode_switch_interval)
     - Heating → skip fan-only logic entirely
  8. Send adjusted_target to AC (target - offset), clamped to min/max
  9. Notify climate entity to update state
```

### Error Handling

- Sensor unavailable → keep last known offset, log warning
- AC entity unavailable → skip cycle, retry next interval
- Graceful degradation, no crash, no log spam

### Startup

- First cycle runs immediately on integration load
- Reads initial state from all entities
- If AC is off → no calibration, just mirror state

## Out of Scope

- Multi-AC grouping (use HA scenes/automations)
- PID control or machine learning
- Boiler, valve, or radiator support
- Remote override detection (future consideration)
- Custom presets (reuse source AC presets)
