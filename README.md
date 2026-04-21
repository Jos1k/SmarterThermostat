# SmarterThermostat

A Home Assistant custom integration that makes your AC smarter by using external temperature sensors to calibrate the target temperature automatically.

## What It Does

Most AC units measure temperature at the indoor unit, which is often near the ceiling or in a poor location. SmarterThermostat compensates for this by:

1. Reading the **actual room temperature** from an external sensor you place where it matters
2. Reading the **outside temperature** to account for environmental load
3. Calculating a **calibration offset** and adjusting the target temperature sent to your AC

Your AC thinks it's targeting 20°C, but SmarterThermostat calculated that sending 20°C will actually achieve the 24°C you wanted — because the room sensor says it's warmer than the AC thinks.

**It never turns your AC on or off.** It only adjusts the target temperature. All HVAC modes, fan speeds, swing modes, and presets from your AC are fully preserved.

## Features

- **Offset-based calibration** — adjusts target temp based on room sensor vs AC sensor difference
- **Outside temperature compensation** — accounts for heat load from outdoor conditions
- **Dead-band fan-only mode** — switches to fan-only when the room is close enough to target (cooling mode only), saving energy while maintaining airflow
- **Compressor protection** — enforces minimum interval between mode switches
- **Full AC proxy** — all fan modes, swing modes, presets, and HVAC modes pass through from your physical AC
- **Runtime tuning** — all parameters adjustable live via number entities (no restart needed)
- **Per-AC instance** — add one integration entry per AC unit

## Requirements

- Home Assistant 2024.1+
- A climate entity for your AC (any integration — Smartir, ESPHome, Tuya, etc.)
- A room temperature sensor (any `sensor` with `device_class: temperature`)
- An outside temperature sensor (weather integration, outdoor sensor, etc.)

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "SmarterThermostat" and install
3. Restart Home Assistant

### Manual

1. Copy the `custom_components/smarter_thermostat` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Smarter Thermostat**
3. Select your:
   - **Source AC** — the physical climate entity to control
   - **Room temperature sensor** — placed where you want accurate readings
   - **Outside temperature sensor** — outdoor temperature source

That's it. A virtual thermostat entity appears that you use instead of the original AC entity.

## How It Works

Every update cycle (default: 60 seconds), the coordinator:

1. Reads room temperature, AC's built-in temperature, and outside temperature
2. Calculates a calibration offset:
   ```
   sensor_offset = (room_temp - ac_temp) * calibration_weight
   outside_factor = (outside_temp - 25°C) * outside_temp_weight * 0.1
   total_offset = sensor_offset + outside_factor  (clamped to ±max_offset)
   ```
3. Adjusts the target: `adjusted_target = your_target - offset`
4. Sends the adjusted target to your physical AC
5. If dead-band fan-only is enabled and room temp is within the dead band of target, switches to fan-only mode (cooling only)

### Example

- You set target to **24°C**
- Room sensor reads **26°C**, AC sensor reads **24°C**, outside is **35°C**
- Sensor offset: `(26 - 24) * 0.8 = 1.6`
- Outside factor: `(35 - 25) * 0.3 * 0.1 = 0.3`
- Total offset: `1.9`
- Adjusted target sent to AC: `24 - 1.9 = 22.1°C`

The AC runs harder because SmarterThermostat knows the room is actually warmer than the AC thinks.

## Entities

Each integration instance creates:

| Entity | Type | Description |
|--------|------|-------------|
| `climate.{name}` | Climate | Virtual thermostat — use this instead of your AC |
| `switch.{name}_calibration` | Switch | Enable/disable calibration (passthrough when off) |
| `switch.{name}_fan_only` | Switch | Enable/disable dead-band fan-only switching |
| `number.{name}_calibration_weight` | Number | Room vs AC sensor weight (0.0–1.0, default 0.8) |
| `number.{name}_outside_temp_weight` | Number | Outside temp influence (0.0–1.0, default 0.3) |
| `number.{name}_dead_band` | Number | Fan-only trigger zone (0.5–3.0°C, default 1.0) |
| `number.{name}_min_offset_change` | Number | Minimum offset change to apply (0.1–2.0, default 0.5) |
| `number.{name}_update_interval` | Number | Polling interval (10–300s, default 60) |
| `number.{name}_max_offset` | Number | Maximum offset clamp (1.0–10.0°C, default 5.0) |
| `number.{name}_min_mode_switch_interval` | Number | Compressor protection (60–600s, default 180) |

## Configuration

Initial setup is done via the UI config flow. All tuning parameters can be adjusted two ways:

- **Number entities** — adjust live from dashboards, automations, or scripts
- **Options flow** — Settings > Devices & Services > Smarter Thermostat > Configure

Changes via number entities take effect immediately. Changes via options flow require a reload.

## Tips

### Multiple ACs

Add one integration entry per AC. Use HA scenes or automations to coordinate them:

```yaml
# Example: Set all ACs to 24°C
automation:
  - alias: "Set all ACs to cool mode"
    trigger: ...
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.living_room_smart
            - climate.bedroom_smart
            - climate.office_smart
        data:
          temperature: 24
```

### Disable Calibration Temporarily

Turn off the calibration switch. The virtual thermostat becomes a pure passthrough to your AC — same target temp, same everything.

### Tuning

Start with defaults and adjust based on your environment:

- **`calibration_weight`** — increase if your AC sensor is very inaccurate, decrease if room and AC sensors are close
- **`outside_temp_weight`** — increase in climates with extreme outdoor temps, decrease in mild climates
- **`dead_band`** — increase for more fan-only time (energy saving), decrease for tighter temperature control
- **`max_offset`** — safety limit; rarely needs changing unless sensors are very far apart

## License

MIT
