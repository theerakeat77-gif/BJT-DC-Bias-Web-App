"""Flask layer for the combined Lab 03 / Lab 04 BJT web app.

One dropdown selects the topology/analysis. Lab 03 modes use the analytical
``dc_bias.py`` engine; Lab 04 CE-amplifier modes use the real ngspice adapter.
This module only handles HTTP concerns, validation and rendering.
"""

from collections.abc import Mapping
import math

from flask import Flask, render_template, request

import spice_engine
from plots import line_chart

from dc_bias import (
    BiasInput,
    BIAS_DIVIDER,
    BIAS_EMITTER,
    BIAS_FIXED,
    BIAS_MODES,
    calculate_dc_bias,
)

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

RESISTOR_FIELDS = ("r1", "r2", "rc", "re")

NUMERIC_ERROR = "ต้องเป็นตัวเลข"
POSITIVE_ERROR = "ต้องมากกว่า 0"

LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
    "rb": "RB",
    "mode": "โหมดวงจร",
}

# All choices live in ONE dropdown. The first three are analytical Lab 03
# topologies; the last three are the same CE voltage-divider circuit solved by
# ngspice with different analyses.
CE_ANALYSES = {
    "ce-dc": "dc",
    "ce-ac": "ac",
    "ce-tran": "transient",
}
ANALYSIS_TO_MODE = {analysis: mode for mode, analysis in CE_ANALYSES.items()}
ALL_MODES = ("divider", "fixed", "emitter", "ce-dc", "ce-ac", "ce-tran")

MODE_LABELS = {
    BIAS_DIVIDER: "Voltage Divider",
    BIAS_FIXED: "Fixed Bias",
    BIAS_EMITTER: "Emitter Bias",
    **{mode: f"CE Amplifier ({analysis})" for mode, analysis in CE_ANALYSES.items()},
}

# ฟิลด์ resistance ที่จำเป็นต่อแต่ละโหมด Lab 03
MODE_RESISTOR_FIELDS = {
    BIAS_DIVIDER: ("r1", "r2", "rc", "re"),
    BIAS_FIXED: ("rb", "rc"),
    BIAS_EMITTER: ("rb", "rc", "re"),
}

DEFAULTS = {
    "mode": BIAS_DIVIDER,
    "vcc": "12",
    "r1": "100k",
    "r2": "22k",
    "rc": "2.2k",
    "re": "1k",
    "beta": "100",
    "vbe": "0.70",
    "rb": "",
}

SIM_FIELDS = (
    "vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout",
    "amplitude", "frequency", "analysis",
)

SIM_DEFAULTS = {
    "rl": "10k",
    "cin": "10u",
    "cout": "10u",
    "amplitude": "0.01",
    "frequency": "1k",
    "analysis": "dc",
}

UNIFIED_DEFAULTS = {**DEFAULTS, **SIM_DEFAULTS}
ALL_FIELDS = FIELDS + (
    "mode", "rb", "rl", "cin", "cout", "amplitude", "frequency", "analysis",
)

ANALYTICAL_BETA = 100.0
ANALYTICAL_VBE = 0.70

app = Flask(__name__)


def parse_float(text: str) -> float:
    """Convert a plain decimal string to a finite float, raising ValueError otherwise."""
    try:
        value = float(text.strip())
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"ไม่ใช่ตัวเลข: {text!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"ไม่ใช่จำนวนจริงจำกัด: {text!r}")
    return value


def _split_resistance(text: str) -> tuple[str, float]:
    """Strip a k/K/M suffix and return the remaining number with its multiplier."""
    raw = text.strip()
    if raw.endswith(("k", "K")):
        return raw[:-1], 1e3
    if raw.endswith("M"):
        return raw[:-1], 1e6
    return raw, 1.0


def parse_resistance(text: str) -> float:
    """Parse a resistance such as ``100000``, ``100k``, ``2.2K`` or ``1M`` (ohms).

    Raises ValueError for non-numeric, non-finite or non-positive values.
    """
    number, multiplier = _split_resistance(text)
    value = parse_float(number) * multiplier
    if not math.isfinite(value):
        raise ValueError(NUMERIC_ERROR)
    if value <= 0:
        raise ValueError(POSITIVE_ERROR)
    return value


def parsed_resistances(form: Mapping[str, str]) -> dict[str, float]:
    """Return the interpreted ohms for every resistor field that parses."""
    parsed: dict[str, float] = {}
    for name in RESISTOR_FIELDS + ("rb",):
        raw = (form.get(name) or "").strip()
        if not raw:
            continue
        try:
            parsed[name] = parse_resistance(raw)
        except ValueError:
            continue
    return parsed


def collect_inputs(form: Mapping[str, str]) -> tuple[BiasInput | None, list[str]]:
    """Validate the submitted form and build a BiasInput for Lab 03 modes."""
    errors: list[str] = []
    values: dict[str, float] = {}

    mode = (form.get("mode") or BIAS_DIVIDER).strip()
    if mode not in BIAS_MODES:
        errors.append(f"{LABELS['mode']} {NUMERIC_ERROR}")
        mode = BIAS_DIVIDER
    values["mode"] = mode

    for name in ("vcc", "beta", "vbe"):
        label = LABELS[name]
        raw = (form.get(name) or "").strip()
        if not raw:
            errors.append(f"กรุณากรอก {label}")
            continue
        try:
            value = parse_float(raw)
        except ValueError:
            errors.append(f"{label} {NUMERIC_ERROR}")
            continue
        if name != "vbe" and value <= 0:
            errors.append(f"{label} {POSITIVE_ERROR}")
            continue
        values[name] = value

    for name in MODE_RESISTOR_FIELDS[mode]:
        label = LABELS[name]
        raw = (form.get(name) or "").strip()
        if not raw:
            errors.append(f"กรุณากรอก {label}")
            continue
        try:
            value = parse_resistance(raw)
        except ValueError as exc:
            reason = POSITIVE_ERROR if str(exc) == POSITIVE_ERROR else NUMERIC_ERROR
            errors.append(f"{label} {reason}")
            continue
        values[name] = value

    for name in RESISTOR_FIELDS + ("rb",):
        if name not in values:
            values[name] = 0.0

    if "vbe" in values and "vcc" in values:
        if values["vbe"] < 0 or values["vbe"] >= values["vcc"]:
            errors.append("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    if errors:
        return None, errors

    return BiasInput(**values), []


def _unified_form(raw: Mapping[str, str] | None = None) -> dict[str, str]:
    """Merge a submitted form with defaults, keeping the single dropdown in sync.

    Legacy ``/simulate`` callers send ``analysis`` instead of a CE mode; that
    value is translated so the rendered dropdown shows the matching option.
    """
    form = dict(UNIFIED_DEFAULTS)
    if raw:
        for key in ALL_FIELDS:
            if key in raw:
                form[key] = raw[key]

    mode = (form.get("mode") or "").strip()
    analysis = (form.get("analysis") or "").strip()
    if mode in CE_ANALYSES:
        form["analysis"] = CE_ANALYSES[mode]
    elif mode in BIAS_MODES and not analysis:
        form["analysis"] = "dc"
    elif analysis in ANALYSIS_TO_MODE:
        form["mode"] = ANALYSIS_TO_MODE[analysis]
    return form


def _render_index(
    form=None,
    parsed=None,
    result=None,
    errors=None,
    sim_result=None,
    sim_errors=None,
    sim_plots=None,
    analytical=None,
):
    """Render the one shared page for every route."""
    form = _unified_form(form)
    return render_template(
        "index.html",
        form=form,
        parsed=parsed if parsed is not None else parsed_resistances(form),
        result=result,
        errors=errors or [],
        mode_labels=MODE_LABELS,
        sim_result=sim_result,
        sim_errors=sim_errors or [],
        sim_plots=sim_plots or {},
        analytical=analytical,
        analytical_beta=ANALYTICAL_BETA,
        analytical_vbe=ANALYTICAL_VBE,
    )


def _analytical_reference(spec: spice_engine.SpiceInput):
    """Independent Lab 3 reference: fixed beta/VBE, not the SPICE BJT model."""
    return calculate_dc_bias(BiasInput(
        vcc=spec.vcc, r1=spec.r1, r2=spec.r2, rc=spec.rc, re=spec.re,
        beta=ANALYTICAL_BETA, vbe=ANALYTICAL_VBE, mode=BIAS_DIVIDER, rb=0.0,
    ))


def _simulation_plots(result: spice_engine.SpiceResult) -> dict[str, str]:
    """Turn values already parsed from ngspice into server-rendered SVG."""
    values = result.values
    if result.analysis == "ac":
        return {
            "gain": line_chart(
                [{"name": "|Vout/Vin| (dB)", "color": "#1f6feb",
                  "points": [(p["frequency"], p["gain_db"]) for p in values["points"]]}],
                x_label="Frequency (Hz)", y_label="Gain (dB)", x_log=True,
            ),
            "phase": line_chart(
                [{"name": "Phase (degree)", "color": "#a0458c",
                  "points": [(p["frequency"], p["phase_deg"]) for p in values["points"]]}],
                x_label="Frequency (Hz)", y_label="Phase (°)", x_log=True,
            ),
        }
    if result.analysis == "transient":
        return {
            "waveform": line_chart(
                [
                    {"name": "Vin (V)", "color": "#0f8f8f",
                     "points": [(p["time"], p["vin"]) for p in values["points"]]},
                    {"name": "Vout (V)", "color": "#e07818",
                     "points": [(p["time"], p["vout"]) for p in values["points"]]},
                ],
                x_label="Time (s)", y_label="Voltage (V)",
            ),
        }
    return {}


def _run_analytical(form: dict[str, str]):
    """Render Lab 03 analytical results for the selected topology."""
    parsed = parsed_resistances(form)
    bias_input, errors = collect_inputs(form)
    if errors:
        return _render_index(form=form, parsed=parsed, errors=errors)
    return _render_index(
        form=form, parsed=parsed, result=calculate_dc_bias(bias_input),
    )


def _run_spice(form: dict[str, str]):
    """Validate, run ngspice and render the Lab 04 results for the CE circuit."""
    spice_form = {field: form.get(field, "") for field in SIM_FIELDS}
    if not spice_form.get("analysis"):
        spice_form["analysis"] = CE_ANALYSES.get(form.get("mode"), "dc")
    spec, errors = spice_engine.validate_spice_input(spice_form)
    if errors:
        return _render_index(form=form, sim_errors=errors)

    try:
        result = spice_engine.run_simulation(spec)
    except spice_engine.SpiceError as exc:
        return _render_index(form=form, sim_errors=[str(exc)])

    return _render_index(
        form=form,
        sim_result=result,
        sim_plots=_simulation_plots(result),
        analytical=_analytical_reference(spec),
    )


@app.get("/")
def index():
    return _render_index()


@app.post("/run")
def run():
    """Single entry point used by the unified dropdown form."""
    raw = {field: request.form.get(field, "") for field in ALL_FIELDS}
    form = _unified_form(raw)
    mode = form["mode"]

    if mode in BIAS_MODES:
        return _run_analytical(form)
    if mode in CE_ANALYSES:
        form["analysis"] = CE_ANALYSES[mode]
        return _run_spice(form)

    return _render_index(form=form, errors=[f"{LABELS['mode']} ไม่ถูกต้อง"])


# --- Backwards-compatible routes kept for the existing test-suite/handouts ---

@app.post("/calculate")
def calculate():
    raw = {field: request.form.get(field, "") for field in ALL_FIELDS}
    form = _unified_form(raw)
    return _run_analytical(form)


@app.post("/simulate")
def simulate():
    raw = {field: request.form.get(field, "") for field in ALL_FIELDS}
    form = _unified_form(raw)
    if form["mode"] not in CE_ANALYSES:
        form["mode"] = ANALYSIS_TO_MODE.get(form.get("analysis"), "ce-dc")
    return _run_spice(form)
