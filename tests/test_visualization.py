"""Kiểm thử sơ đồ mô phỏng luôn bám theo kết quả nhiệt động."""

from gas_turbine import CycleInputs, calculate_simple_cycle
from gas_turbine.visualization import _temperature_color, render_engine_simulation


def test_temperature_color_is_clamped() -> None:
    assert _temperature_color(-100, 300, 1_400) == _temperature_color(300, 300, 1_400)
    assert _temperature_color(2_000, 300, 1_400) == _temperature_color(
        1_400, 300, 1_400
    )


def test_simulation_contains_live_cycle_values() -> None:
    result = calculate_simple_cycle(CycleInputs())
    html = render_engine_simulation(result)
    assert "MÁY NÉN" in html
    assert "BUỒNG ĐỐT" in html
    assert "TUA BIN" in html
    assert f"{result.states[2].temperature:.0f} K" in html
    assert f"{result.electric_power / 1_000:.0f} kW" in html
    assert "animation: rotor-spin" in html


def test_simulation_can_be_frozen() -> None:
    result = calculate_simple_cycle(CycleInputs())
    html = render_engine_simulation(result, animate=False)
    assert "animation-play-state: paused" in html

