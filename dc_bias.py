"""DC bias calculations for BJT common-emitter amplifiers.

Supports three bias configurations:
- Voltage Divider Bias (divider) — existing Lab 2 behaviour
- Fixed Bias (fixed) — Lab 03 addition
- Emitter Bias with single supply (emitter) — Lab 03 addition

Pure engineering logic: this module must not know about Flask, HTTP or HTML.
All values are in SI units (volts, amps, ohms).
"""

from dataclasses import dataclass, field

REGION_ACTIVE = "ACTIVE"
REGION_CUTOFF = "CUTOFF"
REGION_SATURATION = "SATURATION"

BIAS_DIVIDER = "divider"
BIAS_FIXED = "fixed"
BIAS_EMITTER = "emitter"

BIAS_MODES = (BIAS_DIVIDER, BIAS_FIXED, BIAS_EMITTER)

VCE_SAT_WARN = 0.3
VCE_FORWARD_ACTIVE_WARN = 0.2

CUTOFF_WARNING = (
    "วงจรอยู่ในช่วง Cutoff (VTH <= VBE): ทรานซิสเตอร์ไม่นำกระแส "
    "ค่าที่แสดงไม่ใช่จุดทำงานแบบ Forward-Active"
)

SATURATION_WARNING = (
    "VCE ต่ำกว่า 0.3 V: วงจรใกล้ Saturation สมการ Forward-Active ใช้ไม่ได้ "
    "ค่าที่แสดงเป็นค่าตามสมการ ไม่ใช่ค่าจริงของวงจร"
)

FORWARD_ACTIVE_WARNING = (
    "VCE ต่ำกว่าหรือเท่ากับ 0.2 V หรือ IB ไม่มากกว่า 0: "
    "แบบจำลอง Forward-Active อาจใช้ได้ไม่ดี ค่าที่แสดงเป็นค่าตามสมการ "
    "ไม่ใช่ค่าจริงของวงจร"
)


@dataclass(frozen=True)
class BiasInput:
    """Circuit parameters in SI units.

    Fields not used by the selected mode are ignored (default 0.0).
    """

    vcc: float = 0.0
    r1: float = 0.0
    r2: float = 0.0
    rc: float = 0.0
    re: float = 0.0
    beta: float = 0.0
    vbe: float = 0.0
    mode: str = BIAS_DIVIDER
    rb: float = 0.0


@dataclass
class BiasResult:
    """DC operating point plus the region verdict."""

    mode: str
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: list[str] = field(default_factory=list)


def _forward_active_warnings(ib: float, vce: float) -> list[str]:
    """Return warnings when the Forward-Active model may not apply (Lab 03)."""
    warnings: list[str] = []
    if ib <= 0:
        warnings.append(
            "กระแสฐาน IB ไม่มากกว่า 0: แบบจำลอง Forward-Active อาจใช้ได้ไม่ดี"
        )
    if vce <= VCE_FORWARD_ACTIVE_WARN:
        warnings.append(
            f"VCE ต่ำกว่าหรือเท่ากับ {VCE_FORWARD_ACTIVE_WARN:g} V: "
            "แบบจำลอง Forward-Active อาจใช้ได้ไม่ดี "
            "ค่าที่แสดงเป็นค่าตามสมการ ไม่ใช่ค่าจริงของวงจร"
        )
    return warnings


def _calculate_divider_bias(inp: BiasInput) -> BiasResult:
    """Voltage Divider Bias (existing Lab 2 behaviour)."""
    if inp.r1 <= 0 or inp.r2 <= 0 or inp.rc <= 0 or inp.re <= 0 or inp.beta <= 0:
        raise ValueError("ค่าอุปกรณ์ต้องมากกว่า 0 ทั้งหมด")

    vth = inp.vcc * inp.r2 / (inp.r1 + inp.r2)
    rth = inp.r1 * inp.r2 / (inp.r1 + inp.r2)

    # Cutoff: the divider cannot turn the base-emitter junction on.
    if vth <= inp.vbe:
        return BiasResult(
            mode=BIAS_DIVIDER,
            vth=vth,
            rth=rth,
            ib=0.0,
            ic=0.0,
            ie=0.0,
            vb=vth,
            ve=0.0,
            vc=inp.vcc,
            vce=inp.vcc,
            region=REGION_CUTOFF,
            warnings=[CUTOFF_WARNING],
        )

    ib = (vth - inp.vbe) / (rth + (inp.beta + 1) * inp.re)
    ic = inp.beta * ib
    ie = (inp.beta + 1) * ib

    ve = ie * inp.re
    vb = ve + inp.vbe
    vc = inp.vcc - ic * inp.rc
    vce = vc - ve

    # Outside forward-active: report the raw equations, never clamp.
    warnings: list[str] = []
    if vce < VCE_SAT_WARN:
        region = REGION_SATURATION
        warnings = [SATURATION_WARNING]
    else:
        region = REGION_ACTIVE
        warnings = []

    return BiasResult(
        mode=BIAS_DIVIDER,
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )


def _calculate_fixed_bias(inp: BiasInput) -> BiasResult:
    """Fixed Bias: IB = (VCC - VBE) / RB, VE = 0 (Lab 03)."""
    if inp.rb <= 0 or inp.rc <= 0 or inp.beta <= 0:
        raise ValueError("ค่า RB, RC และ β ต้องมากกว่า 0")

    ib = (inp.vcc - inp.vbe) / inp.rb
    ic = inp.beta * ib
    ie = (inp.beta + 1) * ib

    ve = 0.0
    vb = ve + inp.vbe
    vc = inp.vcc - ic * inp.rc
    vce = vc - ve

    region = REGION_ACTIVE
    warnings = _forward_active_warnings(ib, vce)

    return BiasResult(
        mode=BIAS_FIXED,
        vth=0.0,
        rth=0.0,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )


def _calculate_emitter_bias(inp: BiasInput) -> BiasResult:
    """Emitter Bias (single supply): IB = (VCC - VBE) / [RB + (β+1)RE] (Lab 03)."""
    if inp.rb <= 0 or inp.rc <= 0 or inp.re <= 0 or inp.beta <= 0:
        raise ValueError("ค่า RB, RC, RE และ β ต้องมากกว่า 0")

    ib = (inp.vcc - inp.vbe) / (inp.rb + (inp.beta + 1) * inp.re)
    ic = inp.beta * ib
    ie = (inp.beta + 1) * ib

    ve = ie * inp.re
    vb = ve + inp.vbe
    vc = inp.vcc - ic * inp.rc
    vce = vc - ve

    region = REGION_ACTIVE
    warnings = _forward_active_warnings(ib, vce)

    return BiasResult(
        mode=BIAS_EMITTER,
        vth=0.0,
        rth=0.0,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=region,
        warnings=warnings,
    )


def calculate_dc_bias(inp: BiasInput) -> BiasResult:
    """Solve the forward-active DC operating point for the selected bias mode.

    Dispatches to the mode-specific calculator. Raises ValueError for
    non-physical component values so callers cannot divide by zero.
    """
    if inp.mode == BIAS_FIXED:
        return _calculate_fixed_bias(inp)
    if inp.mode == BIAS_EMITTER:
        return _calculate_emitter_bias(inp)
    if inp.mode == BIAS_DIVIDER:
        return _calculate_divider_bias(inp)
    raise ValueError(f"โหมดวงจรไม่รู้จัก: {inp.mode}")
