"""DC bias calculations for a BJT common-emitter amplifier (voltage-divider bias).

Pure engineering logic: this module must not know about Flask, HTTP or HTML.
All values are in SI units (volts, amps, ohms).
"""

from dataclasses import dataclass, field

REGION_ACTIVE = "ACTIVE"
REGION_CUTOFF = "CUTOFF"
REGION_SATURATION = "SATURATION"

VCE_SAT_WARN = 0.3


@dataclass(frozen=True)
class BiasInput:
    """Circuit parameters in SI units."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


@dataclass
class BiasResult:
    """DC operating point plus the region verdict."""

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


def calculate_dc_bias(inp: BiasInput) -> BiasResult:
    """Solve the forward-active DC operating point.

    Raises ValueError for non-physical component values so callers cannot
    divide by zero.
    """
    if inp.r1 <= 0 or inp.r2 <= 0 or inp.rc <= 0 or inp.re <= 0 or inp.beta <= 0:
        raise ValueError("ค่าอุปกรณ์ต้องมากกว่า 0 ทั้งหมด")

    vth = inp.vcc * inp.r2 / (inp.r1 + inp.r2)
    rth = inp.r1 * inp.r2 / (inp.r1 + inp.r2)

    ib = (vth - inp.vbe) / (rth + (inp.beta + 1) * inp.re)
    ic = inp.beta * ib
    ie = (inp.beta + 1) * ib

    ve = ie * inp.re
    vb = ve + inp.vbe
    vc = inp.vcc - ic * inp.rc
    vce = vc - ve

    return BiasResult(
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region=REGION_ACTIVE,
        warnings=[],
    )
