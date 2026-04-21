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
