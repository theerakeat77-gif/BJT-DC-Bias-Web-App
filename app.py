"""Flask layer for the BJT DC bias calculator.

This module only handles HTTP concerns and user input: parsing the resistance
suffixes, validating the form and rendering templates. The engineering maths
lives in ``dc_bias.py`` and must stay independent of Flask.
"""

from collections.abc import Mapping

from flask import Flask, render_template, request

from dc_bias import BiasInput, calculate_dc_bias

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

RESISTOR_FIELDS = ("r1", "r2", "rc", "re")

LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

DEFAULTS = {
    "vcc": "12",
    "r1": "100k",
    "r2": "22k",
    "rc": "2.2k",
    "re": "1k",
    "beta": "100",
    "vbe": "0.70",
}

app = Flask(__name__)


def parse_float(text: str) -> float:
    """Convert a plain decimal string to float, raising ValueError otherwise."""
    try:
        return float(text.strip())
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"ไม่ใช่ตัวเลข: {text!r}") from exc


def _split_resistance(text: str) -> tuple[str, float]:
    """Strip a k/K/M suffix and return the remaining number with its multiplier."""
    raw = text.strip()
    if raw.endswith(("k", "K")):
        return raw[:-1], 1e3
    if raw.endswith("M"):
        return raw[:-1], 1e6
    return raw, 1.0


def parse_resistance(text: str) -> float:
    """Parse a resistance such as ``100000``, ``100k``, ``2.2K`` or ``1M`` (ohms)."""
    number, multiplier = _split_resistance(text)
    value = parse_float(number) * multiplier
    if value <= 0:
        raise ValueError("ค่าความต้านทานต้องมากกว่า 0")
    return value


def collect_inputs(form: Mapping[str, str]) -> tuple[BiasInput | None, list[str]]:
    """Validate the submitted form and build a BiasInput.

    Returns ``(BiasInput, [])`` on success or ``(None, errors)`` when any field
    is missing, non-numeric or non-physical.
    """
    errors: list[str] = []
    values: dict[str, float] = {}

    for name in FIELDS:
        label = LABELS[name]
        raw = (form.get(name) or "").strip()
        if not raw:
            errors.append(f"กรุณากรอก {label}")
            continue

        if name in RESISTOR_FIELDS:
            number, multiplier = _split_resistance(raw)
            try:
                value = parse_float(number) * multiplier
            except ValueError:
                errors.append(f"{label} ต้องเป็นตัวเลข")
                continue
            if value <= 0:
                errors.append(f"{label} ต้องมากกว่า 0")
                continue
        else:
            try:
                value = parse_float(raw)
            except ValueError:
                errors.append(f"{label} ต้องเป็นตัวเลข")
                continue
            if name != "vbe" and value <= 0:
                errors.append(f"{label} ต้องมากกว่า 0")
                continue

        values[name] = value

    if "vbe" in values and "vcc" in values:
        if values["vbe"] < 0 or values["vbe"] >= values["vcc"]:
            errors.append("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    if errors:
        return None, errors

    return BiasInput(**values), []


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULTS, result=None, errors=[])


@app.post("/calculate")
def calculate():
    form = {field: request.form.get(field, "") for field in FIELDS}
    bias_input, errors = collect_inputs(request.form)
    if errors:
        return render_template("index.html", form=form, result=None, errors=errors)
    return render_template(
        "index.html",
        form=form,
        result=calculate_dc_bias(bias_input),
        errors=[],
    )
