"""Flask layer for the BJT DC bias calculator.

This module only handles HTTP concerns and user input: parsing the resistance
suffixes, validating the form and rendering templates. The engineering maths
lives in ``dc_bias.py`` and must stay independent of Flask.
"""

from collections.abc import Mapping
import math

from flask import Flask, render_template, request

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

MODE_LABELS = {
    BIAS_DIVIDER: "Voltage Divider",
    BIAS_FIXED: "Fixed Bias",
    BIAS_EMITTER: "Emitter Bias",
}

# ฟิลด์ resistance ที่จำเป็นต่อแต่ละโหมด
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
    """Validate the submitted form and build a BiasInput.

    Returns ``(BiasInput, [])`` on success or ``(None, errors)`` when any field
    is missing, non-numeric or non-physical. Only fields required by the
    selected bias mode are validated.
    """
    errors: list[str] = []
    values: dict[str, float] = {}

    # ---- โหมดวงจร (ต้องอ่านก่อน เพราะกำหนดฟิลด์ที่ต้องตรวจ) ----
    mode = (form.get("mode") or BIAS_DIVIDER).strip()
    if mode not in BIAS_MODES:
        errors.append(f"{LABELS['mode']} {NUMERIC_ERROR}")
        mode = BIAS_DIVIDER
    values["mode"] = mode

    # ---- ฟิลด์ร่วมทุกโหมด: VCC, β, VBE (RC ตรวจเป็น resistor ตามโหมด) ----
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

    # ---- ฟิลด์เฉพาะโหมด ----
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

    # ฟิลด์ที่ไม่ใช้ในโหมดนี้ ให้ค่าเริ่มต้น 0
    for name in RESISTOR_FIELDS + ("rb",):
        if name not in values:
            values[name] = 0.0

    # ---- VBE ต้องอยู่ในช่วง [0, VCC) ----
    if "vbe" in values and "vcc" in values:
        if values["vbe"] < 0 or values["vbe"] >= values["vcc"]:
            errors.append("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    if errors:
        return None, errors

    return BiasInput(**values), []


@app.get("/")
def index():
    return render_template(
        "index.html",
        form=DEFAULTS,
        parsed=parsed_resistances(DEFAULTS),
        result=None,
        errors=[],
        mode_labels=MODE_LABELS,
    )


@app.post("/calculate")
def calculate():
    form = {field: request.form.get(field, "") for field in FIELDS + ("mode", "rb")}
    parsed = parsed_resistances(form)
    bias_input, errors = collect_inputs(request.form)
    if errors:
        return render_template(
            "index.html", form=form, parsed=parsed, result=None, errors=errors,
            mode_labels=MODE_LABELS,
        )
    return render_template(
        "index.html",
        form=form,
        parsed=parsed,
        result=calculate_dc_bias(bias_input),
        errors=[],
        mode_labels=MODE_LABELS,
    )
