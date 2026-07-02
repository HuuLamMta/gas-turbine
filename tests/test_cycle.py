"""Kiểm thử hồi quy và công thức chu trình Brayton."""

import math

import pytest

from gas_turbine import CycleInputs, calculate_simple_cycle, pressure_ratio_sweep
from gas_turbine.models import InputValidationError


def test_nonideal_compressor_outlet_temperature() -> None:
    inputs = CycleInputs()
    result = calculate_simple_cycle(inputs)
    t1 = inputs.ambient_temperature
    t2s = t1 * inputs.compressor_pressure_ratio ** (
        (inputs.gamma_air - 1) / inputs.gamma_air
    )
    expected_t2 = t1 + (t2s - t1) / inputs.compressor_efficiency
    assert result.states[1].temperature == pytest.approx(expected_t2)


def test_nonideal_turbine_outlet_temperature() -> None:
    inputs = CycleInputs()
    result = calculate_simple_cycle(inputs)
    p3 = result.states[2].pressure
    p4 = result.states[3].pressure
    t4s = inputs.turbine_inlet_temperature * (p4 / p3) ** (
        (inputs.gamma_gas - 1) / inputs.gamma_gas
    )
    expected_t4 = inputs.turbine_inlet_temperature - inputs.turbine_efficiency * (
        inputs.turbine_inlet_temperature - t4s
    )
    assert result.states[3].temperature == pytest.approx(expected_t4)


def test_combustor_fuel_air_ratio() -> None:
    inputs = CycleInputs()
    result = calculate_simple_cycle(inputs)
    t2 = result.states[1].temperature
    expected = inputs.cp_gas * (inputs.turbine_inlet_temperature - t2) / (
        inputs.combustor_efficiency * inputs.fuel_lhv
        - inputs.cp_gas * inputs.turbine_inlet_temperature
    )
    assert result.fuel_air_ratio == pytest.approx(expected)
    assert 0.01 < result.fuel_air_ratio < 0.05


def test_complete_default_cycle_regression() -> None:
    """Ca chuẩn: πc=10, TIT=1400 K; khóa sai lệch công thức ngoài ý muốn."""

    result = calculate_simple_cycle(CycleInputs())
    assert result.states[1].temperature == pytest.approx(603.657, rel=2e-3)
    assert result.states[3].temperature == pytest.approx(873.520, rel=3e-3)
    assert result.net_specific_work / 1_000 == pytest.approx(294.767, rel=5e-3)
    assert result.thermal_efficiency == pytest.approx(0.30393, rel=1e-2)
    assert result.sfc_kg_per_kwh == pytest.approx(0.27546, rel=2e-2)
    assert result.electric_power == pytest.approx(5_718_473, rel=5e-3)


def test_energy_balance_is_consistent() -> None:
    result = calculate_simple_cycle(CycleInputs())
    expected_net = (
        result.inputs.mechanical_efficiency
        * result.turbine_specific_work_air_basis
        - result.compressor_specific_work
    )
    assert result.net_specific_work == pytest.approx(expected_net)
    assert result.thermal_efficiency == pytest.approx(
        result.net_specific_work / result.heat_input_per_kg_air
    )
    assert math.isfinite(result.sfc_kg_per_kwh)


@pytest.mark.parametrize(
    "inputs, message",
    [
        (CycleInputs(ambient_pressure=0), "Áp suất môi trường"),
        (CycleInputs(compressor_pressure_ratio=1), "Tỷ số nén"),
        (CycleInputs(compressor_efficiency=0), "Hiệu suất máy nén"),
        (CycleInputs(turbine_efficiency=1.1), "Hiệu suất tua bin"),
        (CycleInputs(combustor_pressure_loss=1), "Tổn thất áp suất buồng đốt"),
    ],
)
def test_invalid_inputs_raise_helpful_error(
    inputs: CycleInputs, message: str
) -> None:
    with pytest.raises(InputValidationError, match=message):
        calculate_simple_cycle(inputs)


def test_turbine_inlet_temperature_must_exceed_compressor_outlet() -> None:
    with pytest.raises(InputValidationError, match="Nhiệt độ đầu vào tua bin"):
        calculate_simple_cycle(CycleInputs(turbine_inlet_temperature=500))


def test_pressure_ratio_sweep_returns_valid_and_invalid_points() -> None:
    sweep = pressure_ratio_sweep(CycleInputs(), 2, 60, 30)
    assert len(sweep) == 30
    assert any(point.valid for point in sweep)
    assert all(point.pressure_ratio > 1 for point in sweep)
