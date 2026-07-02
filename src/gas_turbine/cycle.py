"""Bộ giải chu trình Brayton dùng tính chất nhiệt không đổi."""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from .models import (
    CycleInputs,
    CycleResult,
    InputValidationError,
    ThermodynamicState,
)

R_AIR = 287.05
REFERENCE_TEMPERATURE = 288.15
REFERENCE_PRESSURE = 101_325.0


def _relative_entropy(temperature: float, pressure: float, cp: float, gas_r: float) -> float:
    """Entropy tương đối so với trạng thái chuẩn; chỉ dùng để vẽ sơ đồ gần đúng."""

    return cp * log(temperature / REFERENCE_TEMPERATURE) - gas_r * log(
        pressure / REFERENCE_PRESSURE
    )


def calculate_simple_cycle(inputs: CycleInputs) -> CycleResult:
    """Tính chu trình Brayton hở, một trục, giãn nở đến áp suất đường xả.

    Giả thiết: trạng thái ổn định, khí lý tưởng, cp và gamma không đổi, cháy hoàn
    toàn; bỏ qua động năng, thế năng và trao đổi nhiệt với môi trường.
    """

    inputs.validate()
    warnings: list[str] = []

    # Cửa vào và máy nén
    t1 = inputs.ambient_temperature
    p1 = inputs.ambient_pressure * inputs.inlet_pressure_recovery
    p2 = p1 * inputs.compressor_pressure_ratio
    exponent_air = (inputs.gamma_air - 1.0) / inputs.gamma_air
    t2s = t1 * inputs.compressor_pressure_ratio**exponent_air
    t2 = t1 + (t2s - t1) / inputs.compressor_efficiency
    compressor_work = inputs.cp_air * (t2 - t1)

    # Buồng đốt
    t3 = inputs.turbine_inlet_temperature
    p3 = p2 * (1.0 - inputs.combustor_pressure_loss)
    if t3 <= t2:
        raise InputValidationError(
            "Nhiệt độ đầu vào tua bin phải lớn hơn nhiệt độ ra máy nén "
            f"({t2:.1f} K)."
        )

    fuel_denominator = (
        inputs.combustor_efficiency * inputs.fuel_lhv - inputs.cp_gas * t3
    )
    if fuel_denominator <= 0:
        raise InputValidationError(
            "Nhiệt trị và hiệu suất buồng đốt không đủ để đạt nhiệt độ yêu cầu."
        )
    fuel_air_ratio = inputs.cp_gas * (t3 - t2) / fuel_denominator
    if not 0 < fuel_air_ratio < 1:
        raise InputValidationError("Tỷ lệ nhiên liệu/không khí tính được không hợp lệ.")
    if fuel_air_ratio > 0.08:
        warnings.append(
            "Tỷ lệ nhiên liệu/không khí lớn hơn 0,08; nên kiểm tra TIT và nhiệt trị."
        )

    # Áp suất trước tổn thất đường xả phải đủ để thắng áp suất môi trường.
    p4 = inputs.ambient_pressure / (1.0 - inputs.exhaust_pressure_loss)
    if p3 <= p4:
        raise InputValidationError(
            "Áp suất sau buồng đốt không đủ để tua bin giãn nở về môi trường. "
            "Hãy tăng tỷ số nén hoặc giảm tổn thất áp suất."
        )

    exponent_gas = (inputs.gamma_gas - 1.0) / inputs.gamma_gas
    t4s = t3 * (p4 / p3) ** exponent_gas
    t4 = t3 - inputs.turbine_efficiency * (t3 - t4s)
    turbine_work_gas = inputs.cp_gas * (t3 - t4)
    turbine_work_air_basis = (1.0 + fuel_air_ratio) * turbine_work_gas

    # Công cơ khí hữu ích sau tổn thất trục, tính trên 1 kg không khí.
    net_work = (
        inputs.mechanical_efficiency * turbine_work_air_basis - compressor_work
    )
    heat_input = fuel_air_ratio * inputs.fuel_lhv
    if net_work <= 0:
        raise InputValidationError(
            "Công riêng hữu ích không dương; chu trình không thể tự duy trì tải."
        )

    thermal_efficiency = net_work / heat_input
    back_work_ratio = compressor_work / turbine_work_air_basis
    sfc = fuel_air_ratio / net_work * 3_600_000.0
    shaft_power = inputs.air_mass_flow * net_work
    electric_power = shaft_power * inputs.generator_efficiency

    if thermal_efficiency > 0.65:
        warnings.append(
            "Hiệu suất nhiệt vượt 65%; cần kiểm tra giả thiết tính chất không đổi."
        )
    if t4 < inputs.ambient_temperature:
        warnings.append("Nhiệt độ khí xả thấp hơn môi trường, kết quả có thể phi thực tế.")

    gas_r = inputs.cp_gas * (inputs.gamma_gas - 1.0) / inputs.gamma_gas
    mass_air = inputs.air_mass_flow
    mass_gas = mass_air * (1.0 + fuel_air_ratio)
    states = (
        ThermodynamicState(
            "1",
            "Vào máy nén",
            t1,
            p1,
            mass_air,
            specific_enthalpy=inputs.cp_air * t1,
            relative_entropy=_relative_entropy(t1, p1, inputs.cp_air, R_AIR),
            notes="Sau tổn thất cửa vào",
        ),
        ThermodynamicState(
            "2",
            "Ra máy nén",
            t2,
            p2,
            mass_air,
            specific_enthalpy=inputs.cp_air * t2,
            relative_entropy=_relative_entropy(t2, p2, inputs.cp_air, R_AIR),
            notes=f"T2s = {t2s:.2f} K",
        ),
        ThermodynamicState(
            "3",
            "Vào tua bin",
            t3,
            p3,
            mass_gas,
            fuel_air_ratio=fuel_air_ratio,
            specific_enthalpy=inputs.cp_gas * t3,
            relative_entropy=_relative_entropy(t3, p3, inputs.cp_gas, gas_r),
            notes="Sau buồng đốt",
        ),
        ThermodynamicState(
            "4",
            "Ra tua bin",
            t4,
            p4,
            mass_gas,
            fuel_air_ratio=fuel_air_ratio,
            specific_enthalpy=inputs.cp_gas * t4,
            relative_entropy=_relative_entropy(t4, p4, inputs.cp_gas, gas_r),
            notes=f"T4s = {t4s:.2f} K; trước tổn thất đường xả",
        ),
    )

    return CycleResult(
        inputs=inputs,
        states=states,
        compressor_specific_work=compressor_work,
        turbine_specific_work_gas=turbine_work_gas,
        turbine_specific_work_air_basis=turbine_work_air_basis,
        net_specific_work=net_work,
        heat_input_per_kg_air=heat_input,
        fuel_air_ratio=fuel_air_ratio,
        thermal_efficiency=thermal_efficiency,
        back_work_ratio=back_work_ratio,
        sfc_kg_per_kwh=sfc,
        shaft_power=shaft_power,
        electric_power=electric_power,
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class SweepPoint:
    pressure_ratio: float
    thermal_efficiency: float | None
    net_specific_work: float | None
    valid: bool
    message: str = ""


def pressure_ratio_sweep(
    base_inputs: CycleInputs,
    start: float = 2.0,
    stop: float = 30.0,
    points: int = 57,
) -> tuple[SweepPoint, ...]:
    """Quét tỷ số nén; giữ lại cả điểm bất khả thi để người dùng nhận biết."""

    if start <= 1 or stop <= start or points < 2:
        raise InputValidationError("Miền quét tỷ số nén không hợp lệ.")

    step = (stop - start) / (points - 1)
    output: list[SweepPoint] = []
    for index in range(points):
        pressure_ratio = start + index * step
        try:
            result = calculate_simple_cycle(
                base_inputs.with_pressure_ratio(pressure_ratio)
            )
            output.append(
                SweepPoint(
                    pressure_ratio,
                    result.thermal_efficiency,
                    result.net_specific_work,
                    True,
                )
            )
        except InputValidationError as exc:
            output.append(SweepPoint(pressure_ratio, None, None, False, str(exc)))
    return tuple(output)

