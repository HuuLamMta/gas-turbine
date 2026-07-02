"""Mô hình dữ liệu có tên và kiểm tra đầu vào kỹ thuật."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import isfinite


class InputValidationError(ValueError):
    """Lỗi đầu vào có thông báo phù hợp cho người dùng kỹ thuật."""


@dataclass(frozen=True)
class CycleInputs:
    """Đầu vào chu trình Brayton không lý tưởng, dùng đơn vị SI."""

    ambient_temperature: float = 288.15
    ambient_pressure: float = 101_325.0
    compressor_pressure_ratio: float = 10.0
    turbine_inlet_temperature: float = 1_400.0
    air_mass_flow: float = 20.0

    compressor_efficiency: float = 0.85
    turbine_efficiency: float = 0.88
    combustor_efficiency: float = 0.98
    mechanical_efficiency: float = 0.99
    generator_efficiency: float = 0.97
    inlet_pressure_recovery: float = 0.99
    combustor_pressure_loss: float = 0.04
    exhaust_pressure_loss: float = 0.02

    fuel_lhv: float = 43_000_000.0
    cp_air: float = 1_005.0
    gamma_air: float = 1.4
    cp_gas: float = 1_148.0
    gamma_gas: float = 1.333

    def validate(self) -> None:
        values = vars(self)
        for name, value in values.items():
            if not isfinite(value):
                raise InputValidationError(
                    f"Lỗi đầu vào: '{name}' phải là một số hữu hạn."
                )

        if self.ambient_temperature <= 0:
            raise InputValidationError("Nhiệt độ môi trường phải lớn hơn 0 K.")
        if self.ambient_pressure <= 0:
            raise InputValidationError("Áp suất môi trường phải lớn hơn 0 Pa.")
        if self.compressor_pressure_ratio <= 1:
            raise InputValidationError("Tỷ số nén máy nén phải lớn hơn 1.")
        if self.turbine_inlet_temperature <= 0:
            raise InputValidationError("Nhiệt độ đầu vào tua bin phải lớn hơn 0 K.")
        if self.air_mass_flow <= 0:
            raise InputValidationError("Lưu lượng không khí phải lớn hơn 0 kg/s.")

        efficiencies = {
            "Hiệu suất máy nén": self.compressor_efficiency,
            "Hiệu suất tua bin": self.turbine_efficiency,
            "Hiệu suất buồng đốt": self.combustor_efficiency,
            "Hiệu suất cơ khí": self.mechanical_efficiency,
            "Hiệu suất máy phát": self.generator_efficiency,
            "Độ phục hồi áp suất cửa vào": self.inlet_pressure_recovery,
        }
        for label, value in efficiencies.items():
            if not 0 < value <= 1:
                raise InputValidationError(
                    f"{label} phải nằm trong khoảng (0, 1]."
                )

        losses = {
            "Tổn thất áp suất buồng đốt": self.combustor_pressure_loss,
            "Tổn thất áp suất đường xả": self.exhaust_pressure_loss,
        }
        for label, value in losses.items():
            if not 0 <= value < 1:
                raise InputValidationError(f"{label} phải nằm trong khoảng [0, 1).")

        if self.fuel_lhv <= 0:
            raise InputValidationError("Nhiệt trị thấp của nhiên liệu phải lớn hơn 0.")
        if self.cp_air <= 0 or self.cp_gas <= 0:
            raise InputValidationError("Nhiệt dung riêng phải lớn hơn 0.")
        if self.gamma_air <= 1 or self.gamma_gas <= 1:
            raise InputValidationError("Số mũ đoạn nhiệt gamma phải lớn hơn 1.")

    def with_pressure_ratio(self, pressure_ratio: float) -> "CycleInputs":
        return replace(self, compressor_pressure_ratio=pressure_ratio)


@dataclass(frozen=True)
class ThermodynamicState:
    station_id: str
    name: str
    temperature: float
    pressure: float
    mass_flow: float
    fuel_air_ratio: float = 0.0
    specific_enthalpy: float | None = None
    relative_entropy: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class CycleResult:
    inputs: CycleInputs
    states: tuple[ThermodynamicState, ...]
    compressor_specific_work: float
    turbine_specific_work_gas: float
    turbine_specific_work_air_basis: float
    net_specific_work: float
    heat_input_per_kg_air: float
    fuel_air_ratio: float
    thermal_efficiency: float
    back_work_ratio: float
    sfc_kg_per_kwh: float
    shaft_power: float
    electric_power: float
    warnings: tuple[str, ...] = field(default_factory=tuple)

