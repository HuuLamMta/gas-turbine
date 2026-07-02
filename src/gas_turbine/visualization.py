"""Sinh sơ đồ SVG động từ kết quả tính toán chu trình."""

from __future__ import annotations

from html import escape

from .models import CycleResult, ThermodynamicState


def _temperature_color(temperature: float, minimum: float, maximum: float) -> str:
    """Ánh xạ nhiệt độ sang dải xanh lam → vàng → đỏ."""

    if maximum <= minimum:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (temperature - minimum) / (maximum - minimum)))

    stops = (
        (0.00, (39, 146, 255)),
        (0.45, (75, 214, 190)),
        (0.70, (255, 196, 61)),
        (1.00, (255, 74, 74)),
    )
    for (left_pos, left_rgb), (right_pos, right_rgb) in zip(stops, stops[1:]):
        if ratio <= right_pos:
            local = (ratio - left_pos) / (right_pos - left_pos)
            rgb = tuple(
                round(left + (right - left) * local)
                for left, right in zip(left_rgb, right_rgb)
            )
            return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"
    return "rgb(255,74,74)"


def _state_card(
    state: ThermodynamicState,
    x: int,
    color: str,
) -> str:
    name = escape(state.name)
    return f"""
      <g class="state-card" transform="translate({x}, 295)">
        <rect width="210" height="92" rx="14" fill="#101b2d" stroke="{color}" stroke-width="2"/>
        <circle cx="20" cy="20" r="7" fill="{color}" class="status-dot"/>
        <text x="36" y="25" class="card-title">Trạm {escape(state.station_id)} · {name}</text>
        <text x="18" y="52" class="card-value">{state.temperature:.1f} K</text>
        <text x="18" y="76" class="card-sub">{state.pressure / 1_000:.1f} kPa · {state.mass_flow:.2f} kg/s</text>
      </g>
    """


def render_engine_simulation(result: CycleResult, animate: bool = True) -> str:
    """Trả HTML chứa sơ đồ động; mọi số liệu lấy trực tiếp từ ``CycleResult``."""

    states = result.states
    temperatures = [state.temperature for state in states]
    colors = [
        _temperature_color(state.temperature, min(temperatures), max(temperatures))
        for state in states
    ]
    max_pressure = max(state.pressure for state in states)
    flow_widths = [
        7.0 + 11.0 * state.pressure / max_pressure
        for state in states
    ]

    # Công tua bin lớn hơn làm rotor quay nhanh hơn, nhưng chặn miền để dễ quan sát.
    turbine_work_kj = result.turbine_specific_work_air_basis / 1_000
    rotor_duration = max(0.55, min(2.2, 700.0 / max(turbine_work_kj, 1.0)))
    motion_state = "running" if animate else "paused"
    expansion_ratio = states[2].pressure / states[3].pressure
    cycle_status = "Ổn định" if not result.warnings else "Cần kiểm tra"
    status_color = "#4ade80" if not result.warnings else "#fbbf24"
    cards = "".join(
        _state_card(state, x, color)
        for state, x, color in zip(states, (25, 310, 675, 965), colors)
    )

    particles = "".join(
        f"""
        <circle r="5" fill="#ffffff" opacity="0.85">
          <animateMotion dur="4.8s" begin="-{offset:.1f}s" repeatCount="indefinite"
            path="M 40 185 C 185 185, 210 185, 325 185 S 520 185, 605 185 S 835 185, 1160 185"/>
        </circle>
        """
        for offset in (0.0, 1.2, 2.4, 3.6)
    )

    return f"""
<div class="engine-shell">
  <style>
    .engine-shell {{
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      color: #e8f0ff;
      background:
        radial-gradient(circle at 72% 30%, rgba(255,120,55,.12), transparent 28%),
        linear-gradient(145deg, #07101e, #0c1727 58%, #08111f);
      border: 1px solid #24344d;
      border-radius: 20px;
      padding: 14px;
      overflow: hidden;
      box-shadow: 0 18px 50px rgba(0,0,0,.24);
    }}
    .engine-header {{
      display: flex; justify-content: space-between; align-items: center;
      gap: 12px; padding: 2px 10px 10px;
    }}
    .engine-title {{ font-weight: 750; font-size: 18px; }}
    .engine-status {{
      display: flex; align-items: center; gap: 8px; padding: 6px 11px;
      border-radius: 999px; background: rgba(255,255,255,.055); font-size: 13px;
    }}
    .engine-status span {{ width: 9px; height: 9px; border-radius: 50%; background: {status_color}; }}
    svg {{ width: 100%; height: auto; display: block; }}
    text {{ fill: #dce8fb; }}
    .component-title {{ font-size: 15px; font-weight: 700; text-anchor: middle; }}
    .component-sub {{ font-size: 12px; fill: #91a4c2; text-anchor: middle; }}
    .card-title {{ font-size: 11px; font-weight: 650; fill: #b9c9e2; }}
    .card-value {{ font-size: 19px; font-weight: 750; fill: #f4f8ff; }}
    .card-sub {{ font-size: 11px; fill: #93a7c5; }}
    .rotor {{ transform-origin: 852px 185px; animation: rotor-spin {rotor_duration:.2f}s linear infinite; }}
    .flow-dash {{ animation: flow-dash 1.2s linear infinite; }}
    .rotor, .flow-dash, circle animateMotion {{ animation-play-state: {motion_state}; }}
    .status-dot {{ animation: pulse 1.7s ease-in-out infinite; animation-play-state: {motion_state}; }}
    @keyframes rotor-spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes flow-dash {{ to {{ stroke-dashoffset: -42; }} }}
    @keyframes pulse {{ 50% {{ opacity: .42; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .rotor, .flow-dash, .status-dot {{ animation: none !important; }}
    }}
  </style>

  <div class="engine-header">
    <div class="engine-title">Mô phỏng trạng thái dòng khí và cụm tua bin</div>
    <div class="engine-status"><span></span>{cycle_status} · {result.shaft_power / 1_000:.0f} kW trục</div>
  </div>

  <svg viewBox="0 0 1200 410" role="img"
       aria-label="Sơ đồ động máy nén, buồng đốt, tua bin và máy phát">
    <defs>
      <linearGradient id="compressorFill" x1="0" x2="1">
        <stop offset="0%" stop-color="{colors[0]}" stop-opacity=".28"/>
        <stop offset="100%" stop-color="{colors[1]}" stop-opacity=".65"/>
      </linearGradient>
      <linearGradient id="combustorFill" x1="0" x2="1">
        <stop offset="0%" stop-color="{colors[1]}" stop-opacity=".38"/>
        <stop offset="100%" stop-color="{colors[2]}" stop-opacity=".70"/>
      </linearGradient>
      <linearGradient id="turbineFill" x1="0" x2="1">
        <stop offset="0%" stop-color="{colors[2]}" stop-opacity=".72"/>
        <stop offset="100%" stop-color="{colors[3]}" stop-opacity=".35"/>
      </linearGradient>
      <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>

    <!-- Đường dòng thể hiện màu nhiệt độ và bề dày tương đối theo áp suất. -->
    <path d="M 35 185 L 190 185" stroke="{colors[0]}" stroke-width="{flow_widths[0]:.1f}" opacity=".65"/>
    <path d="M 340 185 L 480 185" stroke="{colors[1]}" stroke-width="{flow_widths[1]:.1f}" opacity=".65"/>
    <path d="M 680 185 L 755 185" stroke="{colors[2]}" stroke-width="{flow_widths[2]:.1f}" opacity=".72"/>
    <path d="M 950 185 L 1170 185" stroke="{colors[3]}" stroke-width="{flow_widths[3]:.1f}" opacity=".68"/>
    <path class="flow-dash" d="M 35 185 C 185 185, 210 185, 325 185 S 520 185, 605 185 S 835 185, 1170 185"
          fill="none" stroke="#eaf5ff" stroke-width="2" stroke-dasharray="10 32" opacity=".55"/>

    <!-- Máy nén -->
    <path d="M 190 120 L 340 145 L 340 225 L 190 250 Z" fill="url(#compressorFill)"
          stroke="{colors[1]}" stroke-width="2"/>
    <g stroke="#b8d8ef" stroke-width="4" opacity=".82">
      <path d="M220 137 L220 233"/><path d="M252 142 L252 228"/>
      <path d="M284 147 L284 223"/><path d="M316 151 L316 219"/>
    </g>
    <text x="265" y="92" class="component-title">MÁY NÉN</text>
    <text x="265" y="109" class="component-sub">πc = {result.inputs.compressor_pressure_ratio:.2f} · ηc = {result.inputs.compressor_efficiency:.1%}</text>

    <!-- Buồng đốt -->
    <path d="M 480 135 Q 500 115 530 120 L 650 135 Q 680 145 680 185 Q 680 225 650 235 L 530 250 Q 500 255 480 235 Z"
          fill="url(#combustorFill)" stroke="{colors[2]}" stroke-width="2"/>
    <path d="M 555 215 C 530 180 560 175 550 145 C 590 165 575 185 605 190 C 632 195 620 225 590 232 Z"
          fill="#ffb02e" opacity=".92" filter="url(#glow)">
      <animate attributeName="opacity" values=".55;1;.7;.55" dur="1.1s" repeatCount="indefinite"/>
    </path>
    <text x="580" y="92" class="component-title">BUỒNG ĐỐT</text>
    <text x="580" y="109" class="component-sub">f = {result.fuel_air_ratio:.4f} · TIT = {states[2].temperature:.0f} K</text>

    <!-- Tua bin -->
    <path d="M 755 145 L 950 115 L 950 255 L 755 225 Z" fill="url(#turbineFill)"
          stroke="{colors[2]}" stroke-width="2"/>
    <g class="rotor">
      <circle cx="852" cy="185" r="44" fill="#0a1423" stroke="#ffd15a" stroke-width="3"/>
      <g stroke="#e9f2ff" stroke-width="7" stroke-linecap="round">
        <path d="M852 146 L852 224"/><path d="M813 185 L891 185"/>
        <path d="M825 158 L879 212"/><path d="M879 158 L825 212"/>
      </g>
      <circle cx="852" cy="185" r="9" fill="#ffd15a"/>
    </g>
    <text x="852" y="76" class="component-title">TUA BIN</text>
    <text x="852" y="94" class="component-sub">πt = {expansion_ratio:.2f} · wt = {turbine_work_kj:.1f} kJ/kg kk</text>

    <!-- Trục và máy phát -->
    <line x1="852" y1="185" x2="1080" y2="185" stroke="#c7d2e7" stroke-width="8"/>
    <circle cx="1080" cy="185" r="48" fill="#13243c" stroke="#76e4a5" stroke-width="3"/>
    <text x="1080" y="180" class="component-title">G</text>
    <text x="1080" y="200" class="component-sub">{result.electric_power / 1_000:.0f} kW</text>

    {particles}
    {cards}
  </svg>

  <div style="padding:0 12px 7px;color:#8397b6;font-size:12px">
    Màu biểu diễn nhiệt độ tương đối; bề dày dòng biểu diễn áp suất tương đối.
    Tốc độ quay chỉ để trực quan hóa và tỷ lệ nghịch với thời gian quay quy ước, không phải tốc độ trục thực.
  </div>
</div>
"""

