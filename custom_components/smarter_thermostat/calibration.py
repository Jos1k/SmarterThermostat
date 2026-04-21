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
