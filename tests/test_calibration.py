import pytest

from custom_components.smarter_thermostat.calibration import calculate_offset


class TestCalculateOffset:
    def test_no_discrepancy_no_outside_effect(self):
        offset = calculate_offset(
            room_temp=24.0, ac_temp=24.0, outside_temp=25.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        assert offset == 0.0

    def test_room_warmer_than_ac(self):
        offset = calculate_offset(
            room_temp=26.0, ac_temp=24.0, outside_temp=25.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        assert offset == pytest.approx(1.6)

    def test_room_cooler_than_ac(self):
        offset = calculate_offset(
            room_temp=22.0, ac_temp=24.0, outside_temp=25.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        assert offset == pytest.approx(-1.6)

    def test_hot_outside_adds_positive_factor(self):
        offset = calculate_offset(
            room_temp=24.0, ac_temp=24.0, outside_temp=40.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        expected = (40.0 - 25.0) * 0.3 * 0.1
        assert offset == pytest.approx(expected)

    def test_cold_outside_adds_negative_factor(self):
        offset = calculate_offset(
            room_temp=24.0, ac_temp=24.0, outside_temp=10.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        expected = (10.0 - 25.0) * 0.3 * 0.1
        assert offset == pytest.approx(expected)

    def test_combined_sensor_and_outside(self):
        offset = calculate_offset(
            room_temp=26.0, ac_temp=24.0, outside_temp=40.0,
            calibration_weight=0.8, outside_temp_weight=0.3, max_offset=5.0,
        )
        sensor_offset = (26.0 - 24.0) * 0.8
        outside_factor = (40.0 - 25.0) * 0.3 * 0.1
        expected = sensor_offset + outside_factor
        assert offset == pytest.approx(expected)

    def test_clamp_to_max_offset(self):
        offset = calculate_offset(
            room_temp=35.0, ac_temp=24.0, outside_temp=45.0,
            calibration_weight=1.0, outside_temp_weight=1.0, max_offset=5.0,
        )
        assert offset == 5.0

    def test_clamp_to_negative_max_offset(self):
        offset = calculate_offset(
            room_temp=15.0, ac_temp=30.0, outside_temp=0.0,
            calibration_weight=1.0, outside_temp_weight=1.0, max_offset=5.0,
        )
        assert offset == -5.0

    def test_zero_weights(self):
        offset = calculate_offset(
            room_temp=30.0, ac_temp=20.0, outside_temp=40.0,
            calibration_weight=0.0, outside_temp_weight=0.0, max_offset=5.0,
        )
        assert offset == 0.0


class TestCalculateAdjustedTarget:
    def test_basic_adjustment(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target
        adjusted = calculate_adjusted_target(target_temp=24.0, offset=2.0, min_temp=16.0, max_temp=30.0)
        assert adjusted == 22.0

    def test_clamp_to_min(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target
        adjusted = calculate_adjusted_target(target_temp=17.0, offset=3.0, min_temp=16.0, max_temp=30.0)
        assert adjusted == 16.0

    def test_clamp_to_max(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target
        adjusted = calculate_adjusted_target(target_temp=29.0, offset=-3.0, min_temp=16.0, max_temp=30.0)
        assert adjusted == 30.0

    def test_zero_offset(self):
        from custom_components.smarter_thermostat.calibration import calculate_adjusted_target
        adjusted = calculate_adjusted_target(target_temp=24.0, offset=0.0, min_temp=16.0, max_temp=30.0)
        assert adjusted == 24.0
