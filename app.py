"""Giao diện Streamlit cho phần mềm tính chu trình tua bin khí."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent / "src"))

from gas_turbine import CycleInputs, calculate_simple_cycle, pressure_ratio_sweep
from gas_turbine.models import InputValidationError
from gas_turbine.visualization import render_engine_simulation


st.set_page_config(
    page_title="Chu trình tua bin khí",
    page_icon="🔥",
    layout="wide",
)


def percent_input(label: str, default: float, help_text: str | None = None) -> float:
    return (
        st.number_input(
            label,
            min_value=0.01,
            max_value=100.0,
            value=default * 100.0,
            step=0.1,
            help=help_text,
        )
        / 100.0
    )


def state_dataframe(result) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Trạm": state.station_id,
                "Vị trí": state.name,
                "T (K)": state.temperature,
                "P (kPa)": state.pressure / 1_000,
                "h (kJ/kg)": state.specific_enthalpy / 1_000,
                "ṁ (kg/s)": state.mass_flow,
                "f (kg/kg kk)": state.fuel_air_ratio,
                "Ghi chú": state.notes,
            }
            for state in result.states
        ]
    )


st.title("Tính toán chu trình nhiệt động cơ tua bin khí")
st.caption(
    "Chu trình Brayton hở · khí lý tưởng · tính chất nhiệt không đổi · "
    "mô hình nhiên liệu–không khí"
)

with st.sidebar:
    st.header("Thông số đầu vào")
    with st.expander("Môi trường và chế độ", expanded=True):
        ambient_temperature = st.number_input(
            "Nhiệt độ môi trường (K)", 150.0, 400.0, 288.15, 1.0
        )
        ambient_pressure_kpa = st.number_input(
            "Áp suất môi trường (kPa)", 20.0, 150.0, 101.325, 1.0
        )
        air_mass_flow = st.number_input(
            "Lưu lượng không khí (kg/s)", 0.01, 2_000.0, 20.0, 1.0
        )
        inlet_recovery = percent_input("Phục hồi áp suất cửa vào (%)", 0.99)

    with st.expander("Máy nén", expanded=True):
        pressure_ratio = st.number_input("Tỷ số nén πc", 1.01, 80.0, 10.0, 0.5)
        compressor_efficiency = percent_input("Hiệu suất đẳng entropy ηc (%)", 0.85)
        cp_air = st.number_input("cp không khí (J/kg·K)", 100.0, 3_000.0, 1_005.0)
        gamma_air = st.number_input("γ không khí", 1.01, 2.0, 1.400, 0.001)

    with st.expander("Buồng đốt", expanded=True):
        turbine_inlet_temperature = st.number_input(
            "Nhiệt độ vào tua bin TIT (K)", 400.0, 2_500.0, 1_400.0, 10.0
        )
        combustor_efficiency = percent_input("Hiệu suất cháy ηb (%)", 0.98)
        combustor_loss = percent_input("Tổn thất áp suất (%)", 0.04)
        fuel_lhv_mj = st.number_input(
            "Nhiệt trị thấp LHV (MJ/kg)", 1.0, 150.0, 43.0, 0.5
        )

    with st.expander("Tua bin, trục và máy phát", expanded=True):
        turbine_efficiency = percent_input("Hiệu suất đẳng entropy ηt (%)", 0.88)
        mechanical_efficiency = percent_input("Hiệu suất cơ khí ηm (%)", 0.99)
        generator_efficiency = percent_input("Hiệu suất máy phát ηg (%)", 0.97)
        exhaust_loss = percent_input("Tổn thất áp suất đường xả (%)", 0.02)
        cp_gas = st.number_input("cp khí cháy (J/kg·K)", 100.0, 3_000.0, 1_148.0)
        gamma_gas = st.number_input("γ khí cháy", 1.01, 2.0, 1.333, 0.001)

    animate_simulation = st.toggle(
        "Chuyển động mô phỏng",
        value=True,
        help="Tắt để đóng băng dòng khí và rotor khi cần quan sát số liệu.",
    )

inputs = CycleInputs(
    ambient_temperature=ambient_temperature,
    ambient_pressure=ambient_pressure_kpa * 1_000,
    compressor_pressure_ratio=pressure_ratio,
    turbine_inlet_temperature=turbine_inlet_temperature,
    air_mass_flow=air_mass_flow,
    compressor_efficiency=compressor_efficiency,
    turbine_efficiency=turbine_efficiency,
    combustor_efficiency=combustor_efficiency,
    mechanical_efficiency=mechanical_efficiency,
    generator_efficiency=generator_efficiency,
    inlet_pressure_recovery=inlet_recovery,
    combustor_pressure_loss=combustor_loss,
    exhaust_pressure_loss=exhaust_loss,
    fuel_lhv=fuel_lhv_mj * 1_000_000,
    cp_air=cp_air,
    gamma_air=gamma_air,
    cp_gas=cp_gas,
    gamma_gas=gamma_gas,
)

try:
    result = calculate_simple_cycle(inputs)
except InputValidationError as exc:
    st.error(str(exc))
    st.stop()

metric_columns = st.columns(5)
metric_columns[0].metric("Hiệu suất nhiệt", f"{result.thermal_efficiency:.2%}")
metric_columns[1].metric("Công riêng hữu ích", f"{result.net_specific_work / 1_000:.1f} kJ/kg")
metric_columns[2].metric("Công suất trục", f"{result.shaft_power / 1_000:.1f} kW")
metric_columns[3].metric("Công suất điện", f"{result.electric_power / 1_000:.1f} kW")
metric_columns[4].metric("SFC", f"{result.sfc_kg_per_kwh:.3f} kg/kWh")

for warning in result.warnings:
    st.warning(warning)

simulation_tab, overview_tab, station_tab, chart_tab, sweep_tab, assumptions_tab = st.tabs(
    ["Mô phỏng", "Tổng quan", "Bảng trạng thái", "Biểu đồ", "Quét tham số", "Giả thiết"]
)

with simulation_tab:
    components.html(
        render_engine_simulation(result, animate=animate_simulation),
        height=555,
        scrolling=False,
    )
    state_columns = st.columns(4)
    for column, state in zip(state_columns, result.states):
        column.metric(
            f"Trạm {state.station_id} · {state.name}",
            f"{state.temperature:.1f} K",
            f"{state.pressure / 1_000:.1f} kPa",
            delta_color="off",
        )

with overview_tab:
    col1, col2 = st.columns(2)
    performance_df = pd.DataFrame(
        {
            "Đại lượng": [
                "Công máy nén",
                "Công tua bin (quy về kg không khí)",
                "Công riêng hữu ích",
                "Nhiệt cấp từ nhiên liệu",
                "Tỷ lệ nhiên liệu/không khí",
                "Tỷ số công máy nén/tua bin",
            ],
            "Giá trị": [
                f"{result.compressor_specific_work / 1_000:.3f} kJ/kg",
                f"{result.turbine_specific_work_air_basis / 1_000:.3f} kJ/kg",
                f"{result.net_specific_work / 1_000:.3f} kJ/kg",
                f"{result.heat_input_per_kg_air / 1_000:.3f} kJ/kg",
                f"{result.fuel_air_ratio:.6f} kg/kg không khí",
                f"{result.back_work_ratio:.3%}",
            ],
        }
    )
    col1.dataframe(performance_df, hide_index=True, use_container_width=True)
    work_df = pd.DataFrame(
        {
            "Thành phần": ["Tua bin", "Máy nén", "Hữu ích"],
            "Công riêng (kJ/kg)": [
                result.turbine_specific_work_air_basis / 1_000,
                -result.compressor_specific_work / 1_000,
                result.net_specific_work / 1_000,
            ],
        }
    )
    col2.plotly_chart(
        px.bar(
            work_df,
            x="Thành phần",
            y="Công riêng (kJ/kg)",
            color="Thành phần",
            title="Cân bằng công riêng",
        ),
        use_container_width=True,
    )

with station_tab:
    stations_df = state_dataframe(result)
    st.dataframe(
        stations_df.style.format(
            {
                "T (K)": "{:.2f}",
                "P (kPa)": "{:.3f}",
                "h (kJ/kg)": "{:.2f}",
                "ṁ (kg/s)": "{:.3f}",
                "f (kg/kg kk)": "{:.6f}",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.download_button(
        "Tải bảng trạng thái CSV",
        stations_df.to_csv(index=False).encode("utf-8-sig"),
        "bang_trang_thai_tua_bin_khi.csv",
        "text/csv",
    )

with chart_tab:
    col1, col2 = st.columns(2)
    station_labels = [f"{s.station_id} – {s.name}" for s in result.states]
    col1.plotly_chart(
        px.line(
            x=station_labels,
            y=[s.temperature for s in result.states],
            markers=True,
            labels={"x": "Trạm", "y": "Nhiệt độ (K)"},
            title="Phân bố nhiệt độ qua các trạm",
        ),
        use_container_width=True,
    )

    entropy = [s.relative_entropy / 1_000 for s in result.states]
    temperature = [s.temperature for s in result.states]
    # Khép đường về trạm 1 chỉ để minh họa quá trình thải nhiệt của chu trình hở.
    ts_figure = go.Figure(
        go.Scatter(
            x=entropy + [entropy[0]],
            y=temperature + [temperature[0]],
            mode="lines+markers+text",
            text=[s.station_id for s in result.states] + [""],
            textposition="top center",
        )
    )
    ts_figure.update_layout(
        title="Sơ đồ T–s gần đúng",
        xaxis_title="Entropy tương đối (kJ/kg·K)",
        yaxis_title="Nhiệt độ (K)",
    )
    col2.plotly_chart(ts_figure, use_container_width=True)
    st.caption(
        "Sơ đồ T–s chỉ mang tính gần đúng vì mô hình dùng cp, γ không đổi và "
        "hai bộ tính chất khác nhau cho không khí/khí cháy."
    )

with sweep_tab:
    st.subheader("Ảnh hưởng của tỷ số nén")
    sweep_col1, sweep_col2, sweep_col3 = st.columns(3)
    sweep_start = sweep_col1.number_input("πc bắt đầu", 1.1, 79.0, 2.0, 0.5)
    sweep_stop = sweep_col2.number_input("πc kết thúc", 1.2, 80.0, 30.0, 0.5)
    sweep_points = sweep_col3.slider("Số điểm", 10, 150, 57)
    if sweep_stop <= sweep_start:
        st.info("πc kết thúc phải lớn hơn πc bắt đầu.")
    else:
        sweep = pressure_ratio_sweep(inputs, sweep_start, sweep_stop, sweep_points)
        valid_sweep = pd.DataFrame(
            [
                {
                    "Tỷ số nén": point.pressure_ratio,
                    "Hiệu suất nhiệt (%)": point.thermal_efficiency * 100,
                    "Công riêng (kJ/kg)": point.net_specific_work / 1_000,
                }
                for point in sweep
                if point.valid
            ]
        )
        if valid_sweep.empty:
            st.warning("Không có điểm khả thi trong miền quét.")
        else:
            sweep_plot = px.line(
                valid_sweep,
                x="Tỷ số nén",
                y=["Hiệu suất nhiệt (%)", "Công riêng (kJ/kg)"],
                markers=False,
                title="Hiệu suất và công riêng theo tỷ số nén",
            )
            sweep_plot.update_layout(legend_title_text="Đại lượng")
            st.plotly_chart(sweep_plot, use_container_width=True)
            best_eff = valid_sweep.loc[valid_sweep["Hiệu suất nhiệt (%)"].idxmax()]
            best_work = valid_sweep.loc[valid_sweep["Công riêng (kJ/kg)"].idxmax()]
            st.info(
                f"Trong miền quét: η lớn nhất tại πc ≈ {best_eff['Tỷ số nén']:.2f}; "
                f"công riêng lớn nhất tại πc ≈ {best_work['Tỷ số nén']:.2f}."
            )

with assumptions_tab:
    st.markdown(
        """
- Dòng ổn định; không khí và khí cháy được xem là khí lý tưởng.
- `cp` và `γ` không đổi trong từng miền; không xét phân ly hóa học.
- Cháy hoàn toàn; tỷ lệ nhiên liệu được xác định từ cân bằng năng lượng buồng đốt.
- Bỏ qua động năng, thế năng và truyền nhiệt qua vỏ thiết bị.
- Tua bin giãn nở đến áp suất đủ thắng tổn thất đường xả và áp suất môi trường.
- Công trục hữu ích = công tua bin sau tổn thất cơ khí − công máy nén.

Ứng dụng phục vụ học tập, phân tích và thiết kế sơ bộ; không phải phần mềm được
chứng nhận cho vận hành hay thiết kế an toàn động cơ thực.
"""
    )
