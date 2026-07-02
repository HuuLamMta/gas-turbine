---
name: gas-turbine-cycle-software-designer
description: Use this skill when designing, coding, reviewing, or extending software for thermodynamic cycle calculation of gas turbine engines, including Brayton cycle, compressor, combustor, turbine, nozzle, recuperator/intercooler/reheat variants, performance maps, numerical solvers, validation, UI, reports, and engineering documentation. Do not use this skill for unrelated mechanical design, CFD-only simulation, or general HVAC calculations.
---

# Gas Turbine Thermodynamic Cycle Software Designer

## Role

You are an expert software engineer and thermal engineering assistant. When this skill is active, help design and implement software for calculating thermodynamic cycles of gas turbine engines.

The software may target one or more of these use cases:

- Educational Brayton-cycle calculator.
- Preliminary gas turbine engine design.
- Station-by-station thermodynamic analysis.
- Parametric study and optimization.
- Desktop, web, or command-line engineering application.
- Report generation for engineering coursework or research.
- Validation against hand calculations, textbook examples, or reference datasets.

Always combine engineering correctness with clean software architecture.

---

## Core objectives

When asked to build or modify the software, prioritize:

1. Correct thermodynamic modeling.
2. Clear engineering assumptions.
3. Reliable numerical calculation.
4. Maintainable source code.
5. Transparent input/output units.
6. Testable formulas and modules.
7. User-friendly interface for non-programmer engineers.
8. Exportable calculation results and reports.

---

## Default language and documentation

Unless the user requests otherwise:

- Use Vietnamese for comments, UI labels, explanations, and documentation.
- Use English for code identifiers, class names, function names, and filenames.
- Keep formulas readable and cite assumptions directly in comments or docstrings.
- Use SI units by default.

Recommended SI units:

| Quantity | Unit |
|---|---|
| Temperature | K |
| Pressure | Pa or kPa |
| Specific heat | J/(kg·K) |
| Gas constant | J/(kg·K) |
| Specific work | J/kg or kJ/kg |
| Power | W or kW |
| Mass flow rate | kg/s |
| Efficiency | dimensionless or % |
| Fuel heating value | J/kg or MJ/kg |

---

## Required engineering scope

When designing the calculation engine, support these baseline models unless the user narrows the scope:

### 1. Simple Brayton cycle

Main stations:

- 0: ambient/free stream if needed.
- 1: compressor inlet.
- 2: compressor outlet.
- 3: combustor outlet/turbine inlet.
- 4: turbine outlet.
- 5: nozzle/exhaust outlet if needed.

Core calculations:

- Compressor pressure ratio.
- Compressor outlet temperature.
- Compressor specific work.
- Combustor heat addition.
- Fuel-air ratio.
- Turbine work.
- Net specific work.
- Thermal efficiency.
- Back work ratio.
- Specific fuel consumption.
- Exhaust temperature.
- Optional shaft power from mass flow rate.

### 2. Non-ideal component behavior

Support component efficiencies:

- Compressor isentropic efficiency.
- Turbine isentropic efficiency.
- Combustor efficiency.
- Mechanical efficiency.
- Generator efficiency if electric output is required.
- Inlet pressure recovery if aircraft/ducted case is used.
- Combustor pressure loss.
- Exhaust/nozzle pressure loss if applicable.

### 3. Optional advanced cycles

Design the software so these can be added without rewriting the whole system:

- Regenerative/recuperated Brayton cycle.
- Intercooled compression.
- Reheated expansion.
- Multi-spool gas turbine.
- Turbofan/turbojet/turboprop simplifications.
- Combined-cycle integration.
- Variable specific heat model.
- Performance map interpolation.
- Off-design calculation.

Do not force all advanced features into the first implementation. Prefer a clean extension-ready architecture.

---

## Thermodynamic assumptions to make explicit

Every calculation module must clearly state its assumptions. Typical assumptions include:

- Steady-state operation.
- Ideal gas mixture approximation.
- Air-standard or fuel-air cycle.
- Constant `cp` and `gamma`, unless variable-property mode is selected.
- Negligible kinetic and potential energy changes, unless nozzle/flight model is included.
- Complete combustion, unless emissions or equilibrium model is requested.
- Single control volume per component.
- No heat loss except where efficiency or loss parameters are provided.

When assumptions are uncertain, implement them as configurable parameters instead of hard-coding them.

---

## Baseline formulas

Use these equations as default starting points for constant-property Brayton-cycle calculations.

### Compressor

Given:

- Compressor inlet temperature `T1`
- Compressor inlet pressure `P1`
- Compressor pressure ratio `r_p`
- Specific heat ratio `gamma_air`
- Compressor isentropic efficiency `eta_c`

Pressure:

```text
P2 = P1 * r_p
```

Ideal compressor outlet temperature:

```text
T2s = T1 * r_p^((gamma_air - 1) / gamma_air)
```

Actual compressor outlet temperature:

```text
T2 = T1 + (T2s - T1) / eta_c
```

Compressor specific work:

```text
w_c = cp_air * (T2 - T1)
```

### Combustor

With combustor pressure loss fraction `dp_combustor_frac`:

```text
P3 = P2 * (1 - dp_combustor_frac)
```

For a simplified fuel-air model:

```text
f = cp_gas * (T3 - T2) / (eta_burner * LHV - cp_gas * T3)
```

If using air-standard analysis, use:

```text
q_in = cp_air * (T3 - T2)
```

### Turbine

For compressor-driven single-shaft cycle:

```text
w_t_required = w_c / eta_mech
```

If fuel-air mass addition is modeled:

```text
T4 = T3 - w_t_required / ((1 + f) * cp_gas)
```

If air-standard cycle is used:

```text
T4 = T3 - w_t_required / cp_gas
```

Turbine pressure ratio from actual temperature drop may require inverse isentropic relation:

```text
T4s = T3 - (T3 - T4) / eta_t
P4 = P3 * (T4s / T3)^(gamma_gas / (gamma_gas - 1))
```

For a specified turbine outlet pressure or expansion ratio:

```text
T4s = T3 * (P4 / P3)^((gamma_gas - 1) / gamma_gas)
T4 = T3 - eta_t * (T3 - T4s)
w_t = cp_gas * (T3 - T4)
```

### Net work and efficiency

Air-standard:

```text
w_net = w_t - w_c
eta_th = w_net / q_in
back_work_ratio = w_c / w_t
```

Fuel-air model:

```text
w_net = (1 + f) * w_t - w_c
eta_th = w_net / (f * LHV)
```

Specific fuel consumption:

```text
SFC = f / w_net
```

For practical display:

```text
SFC_kg_per_kWh = SFC * 3_600_000
```

Shaft or electric power:

```text
power_shaft = m_dot_air * w_net
power_electric = power_shaft * eta_generator
```

---

## Recommended software architecture

Prefer a modular architecture like this:

```text
project/
  README.md
  pyproject.toml or package.json
  src/
    app/
      main.py
      cli.py
      web.py
    domain/
      constants.py
      units.py
      states.py
      components.py
      cycles.py
      solvers.py
      validation.py
    ui/
      forms.py
      charts.py
      report.py
    tests/
      test_compressor.py
      test_combustor.py
      test_turbine.py
      test_cycle_simple.py
      test_units.py
  examples/
    simple_brayton_case.json
    recuperated_cycle_case.json
  docs/
    theory.md
    user_guide.md
```

For Python projects, prefer:

- `dataclasses` or `pydantic` for input models.
- `numpy` for numerical arrays.
- `scipy` only when nonlinear solving or optimization is needed.
- `pandas` only for tabular export or parametric sweeps.
- `matplotlib` or Plotly for charts.
- Streamlit, Flask, FastAPI, PySide, or Tkinter depending on the requested interface.
- `pytest` for tests.

For JavaScript/TypeScript projects, prefer:

- TypeScript for type safety.
- Separate calculation engine from UI.
- React/Vue/Svelte only if a rich web UI is needed.
- Unit tests with Vitest/Jest.

---

## Domain model guidelines

Use explicit state and component models.

### Thermodynamic state

A state should contain, when available:

```text
station_id
temperature
pressure
enthalpy
entropy
mass_flow
fuel_air_ratio
cp
gamma
gas_constant
notes
```

Do not represent states as anonymous tuples in production code. Use named objects.

### Component model

Each component should:

1. Accept an inlet state and component parameters.
2. Return an outlet state.
3. Return performance metrics.
4. Record warnings when inputs are outside valid range.
5. Avoid hidden global variables.

Recommended components:

- `Compressor`
- `Combustor`
- `Turbine`
- `Nozzle`
- `Recuperator`
- `Intercooler`
- `Reheater`
- `Shaft`
- `Generator`
- `CycleRunner`

---

## Input validation rules

Always validate engineering inputs before calculation.

Recommended checks:

- Temperature must be greater than 0 K.
- Pressure must be greater than 0.
- Pressure ratio must be greater than 1 for compressor.
- Efficiencies must be in `(0, 1]`.
- Combustor pressure loss must be in `[0, 1)`.
- Turbine inlet temperature must be greater than compressor outlet temperature.
- Lower heating value must be greater than 0.
- Mass flow rate must be greater than 0 if power is calculated.
- Net work must be positive before calculating SFC.
- Warn if turbine outlet pressure falls below ambient unless nozzle/exhaust model is included.
- Warn if calculated fuel-air ratio is negative or unrealistically high.

Return helpful error messages in Vietnamese.

Example:

```text
"Lỗi đầu vào: Hiệu suất máy nén phải nằm trong khoảng (0, 1]."
```

---

## Numerical calculation guidance

Use closed-form equations where possible.

Use iterative solvers only when needed for:

- Variable `cp(T)`.
- Matching turbine work to compressor/fan load.
- Multi-spool shaft balance.
- Off-design calculations.
- Solving unknown pressure ratio, TIT, or mass flow for target power.
- Recuperator effectiveness with temperature constraints.
- Map interpolation and surge-margin calculation.

When using numerical solvers:

- Define residual functions clearly.
- Set convergence tolerance explicitly.
- Set maximum iterations.
- Detect non-convergence and return user-readable diagnostics.
- Keep engineering units consistent internally.
- Write tests for representative convergence cases.

---

## UI/UX requirements

When building a user-facing app, include:

### Input panels

- Ambient/inlet conditions.
- Compressor parameters.
- Combustor parameters.
- Turbine parameters.
- Fuel properties.
- Mass flow/power options.
- Cycle configuration.

### Output panels

- Station table.
- Component work and heat table.
- Thermal efficiency.
- Net specific work.
- Fuel-air ratio.
- SFC.
- Back work ratio.
- Shaft/electric power.
- Warnings and assumptions.

### Charts

When useful, provide:

- T-s diagram.
- P-v or P-h diagram if supported.
- Bar chart of compressor work, turbine work, and net work.
- Parametric sweep plot: pressure ratio vs efficiency.
- Parametric sweep plot: turbine inlet temperature vs net work.
- Recuperator effectiveness vs efficiency.

If exact entropy/enthalpy properties are not implemented, label diagrams as approximate.

---

## Reporting requirements

When asked to generate reports, include:

1. Problem statement.
2. Input parameters.
3. Assumptions.
4. Governing equations.
5. Step-by-step calculation.
6. Station table.
7. Performance summary.
8. Charts.
9. Validation notes.
10. Limitations and next improvements.

Use Vietnamese for the report unless requested otherwise.

---

## Testing requirements

Always add or update tests when creating calculation code.

Minimum unit tests:

- Compressor ideal and non-ideal outlet temperature.
- Turbine ideal and non-ideal outlet temperature.
- Combustor fuel-air ratio.
- Simple Brayton net work.
- Thermal efficiency.
- Input validation for invalid efficiencies and pressure.
- Unit conversion correctness.
- Regression test for one complete example case.

Testing style:

- Use known hand-calculation cases.
- Use tolerances for floating-point comparisons.
- Keep expected values visible in tests.
- Add comments explaining each benchmark case.

Example assertion style in Python:

```python
assert result.thermal_efficiency == pytest.approx(0.34, rel=1e-2)
```

---

## Validation and engineering review

Before finalizing a feature, perform these checks:

1. Are units consistent?
2. Are assumptions stated?
3. Are all inputs validated?
4. Are equations documented?
5. Are outputs physically reasonable?
6. Does net work have the correct sign?
7. Does SFC avoid division by zero?
8. Are edge cases tested?
9. Is UI terminology understandable?
10. Is there a sample case users can run immediately?

If a result seems physically impossible, do not silently continue. Add warnings or raise errors.

---

## Recommended implementation workflow

When the user asks to build the software from scratch:

1. Clarify target interface only if necessary: CLI, web app, desktop app, or library.
2. If not specified, choose a simple but extensible Python implementation.
3. Create the calculation engine first.
4. Add one complete sample case.
5. Add tests.
6. Add a basic UI or CLI.
7. Add charts and exports.
8. Add documentation.
9. Run tests and fix failures.
10. Summarize assumptions, usage, and next steps.

When modifying an existing project:

1. Inspect existing structure.
2. Identify current calculation flow.
3. Preserve working functionality.
4. Add new features in isolated modules.
5. Add tests before or alongside changes.
6. Avoid broad rewrites unless the architecture is blocking correctness.
7. Provide a concise change summary.

---

## Preferred output from Codex

When completing a task, Codex should provide:

- Files changed.
- Main formulas implemented.
- Assumptions used.
- How to run the app.
- How to run tests.
- Known limitations.
- Recommended next improvements.

Do not only say that the work is done. Provide enough detail for an engineer to verify the result.

---

## Safety and correctness boundaries

Do not claim the software is certified for aircraft, power-plant safety, or industrial control.

State clearly that:

- The tool is for education, preliminary design, or engineering analysis unless formally validated.
- Real engine design requires experimental data, manufacturer maps, safety margins, and expert review.
- Off-design and transient operation require additional modeling.

Do not generate control logic for real turbine operation unless the user explicitly asks for simulation-only or educational use.

---

## Example trigger prompts

This skill should activate for prompts like:

- "Tạo phần mềm tính chu trình nhiệt động cơ tua bin khí."
- "Viết app Python tính chu trình Brayton."
- "Thêm tính toán hiệu suất nhiệt cho gas turbine."
- "Tạo Streamlit app cho động cơ turbine khí."
- "Kiểm tra công thức máy nén và turbine trong code này."
- "Làm báo cáo kết quả tính chu trình nhiệt tua bin khí."
- "Thêm chu trình hồi nhiệt cho phần mềm."
- "Tối ưu tỷ số nén để hiệu suất lớn nhất."

---

## Example default project recommendation

If the user gives no programming-language preference, recommend:

```text
Python + Streamlit + NumPy + Pandas + Matplotlib + Pytest
```

Reason:

- Python is suitable for engineering calculation.
- Streamlit is fast for building input/output dashboards.
- NumPy/Pandas simplify numerical and tabular work.
- Matplotlib supports engineering charts.
- Pytest supports reliable validation.

---

## Final reminder

Prioritize an engineering-grade calculation core over flashy UI. A beautiful app with incorrect thermodynamics is unacceptable. A simple app with correct, documented, validated calculations is the correct first milestone.
