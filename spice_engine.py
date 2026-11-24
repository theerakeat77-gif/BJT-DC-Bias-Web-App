"""Adapter for the real ngspice solver used by Lab 04.

This module is deliberately independent of Flask and of ``dc_bias.py``: it only
builds a netlist from validated numbers, starts ngspice with ``subprocess.run``
(an argument list, never a shell string), parses the raw output that the solver
actually wrote and returns values with provenance. No result is invented here.

Netlist nodes follow the Lab 04 handout: ``vin`` after ``CIN`` (base), ``vc``
at the collector, ``ve`` at the emitter and ``vout`` after ``COUT`` at ``RL``.
"""

from __future__ import annotations

import cmath
from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache

ANALYSES = ("dc", "ac", "transient")

MODEL_NAME = "t2n2222"

# Model card copied verbatim from the ngspice 47 distribution:
# examples/noise/bipolar-noise.cir (T. Tuma, A. Burmen, "Circuit Simulation
# with SPICE OPUS: Theory and Practice", Boston 2009). It is bundled with the
# installed solver so a run is reproducible without inventing parameters.
MODEL_CARD = f".model {MODEL_NAME} npn\n" + "\n".join([
    "+ is=19f bf=150 vaf=100 ikf=0.18 ise=50p",
    "+ ne=2.5 br=7.5 var=6.4 ikr=12m isc=8.7p",
    "+ nc=1.2 rb=50 re=0.4 rc=0.3 cje=26p tf=0.5n",
    "+ cjc=11p tr=7n xtb=1.5 kf=0.032f af=1",
])

AC_START_HZ = 1.0
AC_STOP_HZ = 1e7
AC_DECADES = 20
TRANSIENT_CYCLES = 5
POINTS_PER_CYCLE = 200

NOT_DETERMINED = "not determined in sweep range"


class SpiceError(RuntimeError):
    """Raised whenever the solver or its output cannot be trusted."""


@dataclass(frozen=True)
class SpiceInput:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin: float
    cout: float
    amplitude: float
    frequency: float
    analysis: str = "dc"


@dataclass
class SpiceResult:
    analysis: str
    status: str
    engine: str
    model: str
    netlist: str
    values: dict
    log_excerpt: str = ""
    warnings: list[str] = field(default_factory=list)


def _finite_float(text: object) -> float:
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        value = float(text)
    else:
        value = float(str(text).strip())
    if not math.isfinite(value):
        raise ValueError("not finite")
    return value


def _suffix_number(text: object, *, allow_zero: bool = False) -> float:
    raw = str(text).strip()
    if not raw:
        raise ValueError("missing value")
    multiplier = 1.0
    upper = raw.upper()
    if upper.endswith("MEG"):
        number, multiplier = raw[:-3], 1e6
    elif upper.endswith("K"):
        number, multiplier = raw[:-1], 1e3
    elif upper.endswith("M"):
        number, multiplier = raw[:-1], 1e-3
    elif upper.endswith("U"):
        number, multiplier = raw[:-1], 1e-6
    elif upper.endswith("N"):
        number, multiplier = raw[:-1], 1e-9
    else:
        number = raw
    value = _finite_float(number) * multiplier
    if not allow_zero and value <= 0:
        raise ValueError("must be positive")
    if value < 0:
        raise ValueError("must be positive")
    return value


def validate_spice_input(form) -> tuple[SpiceInput | None, list[str]]:
    """Return a fully numeric SpiceInput or a list of Thai error messages."""
    errors: list[str] = []
    values: dict[str, float] = {}
    labels = {
        "vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC", "re": "RE",
        "rl": "RL", "cin": "Cin", "cout": "Cout",
        "amplitude": "Amplitude", "frequency": "Frequency",
    }
    for name, label in labels.items():
        raw = (form.get(name) or "").strip()
        if not raw:
            errors.append(f"กรุณากรอก {label}")
            continue
        try:
            value = _suffix_number(raw)
        except (TypeError, ValueError):
            errors.append(f"{label} ต้องเป็นตัวเลขบวกและมีหน่วยถูกต้อง")
            continue
        if name == "vcc" and value > 1000:
            errors.append("VCC ต้องไม่เกิน 1000 V")
        if name == "frequency" and value > 1e7:
            errors.append("Frequency ต้องไม่เกิน 10 MHz")
        if name == "amplitude" and value > 100:
            errors.append("Amplitude ต้องไม่เกิน 100 V")
        values[name] = value

    analysis = (form.get("analysis") or "dc").strip()
    if analysis not in ANALYSES:
        errors.append("Analysis mode ไม่ถูกต้อง")
        analysis = "dc"

    if errors:
        return None, errors
    return SpiceInput(analysis=analysis, **values), []


def _fmt(value: float) -> str:
    """Format a validated number with an unambiguous SPICE suffix."""
    value = float(value)
    for scale, suffix in ((1e6, "MEG"), (1e3, "k"), (1.0, ""), (1e-3, "m"),
                          (1e-6, "u"), (1e-9, "n")):
        if value >= scale or scale == 1e-9:
            scaled = value / scale
            text = f"{scaled:.6g}"
            return f"{text}{suffix}"
    return f"{value:.6g}"


def build_netlist(spec: SpiceInput) -> str:
    """Build one analysis deck; every value has already been validated."""
    lines = [
        "* Lab04 CE voltage-divider reference circuit",
        f"* BJT model card: ngspice 47 examples/noise/bipolar-noise.cir ({MODEL_NAME})",
        f"VCC vcc 0 DC {_fmt(spec.vcc)}",
        f"VIN src 0 DC 0 AC {_fmt(spec.amplitude)} "
        f"SIN(0 {_fmt(spec.amplitude)} {_fmt(spec.frequency)})",
        f"CIN src vin {_fmt(spec.cin)}",
        f"COUT vc vout {_fmt(spec.cout)}",
        f"R1 vcc vin {_fmt(spec.r1)}",
        f"R2 vin 0 {_fmt(spec.r2)}",
        f"RC vcc vc {_fmt(spec.rc)}",
        f"RE ve 0 {_fmt(spec.re)}",
        f"RL vout 0 {_fmt(spec.rl)}",
        f"Q1 vc vin ve {MODEL_NAME}",
        MODEL_CARD,
    ]
    if spec.analysis == "dc":
        lines.append(".op")
    elif spec.analysis == "ac":
        lines.append(f".ac dec {AC_DECADES} {_fmt(AC_START_HZ)} {_fmt(AC_STOP_HZ)}")
    elif spec.analysis == "transient":
        period = 1.0 / spec.frequency
        lines.append(f".tran {_fmt(period / POINTS_PER_CYCLE)} "
                     f"{_fmt(period * TRANSIENT_CYCLES)} 0 0")
    else:
        raise SpiceError(f"unknown analysis: {spec.analysis}")
    lines.append(".end")
    return "\n".join(lines) + "\n"


def find_ngspice() -> str | None:
    """Locate the solver from the environment or PATH without modifying either."""
    configured = os.environ.get("NGSPICE_EXECUTABLE", "").strip()
    if configured:
        if Path(configured).is_file() or shutil.which(configured):
            return configured
    for name in ("ngspice", "ngspice_con"):
        found = shutil.which(name)
        if found:
            return found
    return None


@lru_cache(maxsize=8)
def _engine_version(executable: str) -> str:
    try:
        completed = subprocess.run(
            [executable, "--version"], capture_output=True, text=True,
            timeout=10, encoding="utf-8", errors="replace",
        )
        match = re.search(r"ngspice-[\w.]+", completed.stdout + completed.stderr)
        return match.group(0) if match else "ngspice (version unknown)"
    except (OSError, subprocess.SubprocessError):
        return "ngspice (version unknown)"


def parse_raw(raw_text: str) -> dict[str, dict]:
    """Parse the ASCII raw file ngspice writes with ``-r``."""
    plots: dict[str, dict] = {}
    current: dict | None = None
    lines = raw_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("Plotname:"):
            name = line.split(":", 1)[1].strip()
            current = {"variables": [], "points": [], "flags": "real"}
            plots[name] = current
        elif current is not None and line.startswith("Flags:"):
            current["flags"] = line.split(":", 1)[1].strip()
        elif current is not None and line.startswith("Variables:"):
            index += 1
            while index < len(lines) and lines[index].startswith("\t"):
                parts = lines[index].split()
                if len(parts) >= 2:
                    current["variables"].append(parts[1])
                index += 1
            continue
        elif current is not None and line.startswith("Values:"):
            index += 1
            while index < len(lines) and lines[index].strip() and not lines[index].startswith("Title:"):
                row = lines[index]
                skip_index = not row.startswith("\t")
                if skip_index:
                    current["points"].append([])
                for token in row.split("\t"):
                    token = token.strip()
                    if not token:
                        continue
                    if skip_index:
                        skip_index = False
                        continue
                    if "," in token:
                        real, imag = token.split(",", 1)
                        value = complex(float(real), float(imag))
                    else:
                        value = float(token)
                    current["points"][-1].append(value)
                index += 1
            continue
        index += 1
    return plots


def _channel(plot: dict, name: str) -> list:
    column = plot["variables"].index(name)
    return [point[column] for point in plot["points"]]


def _wrap_degrees(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def dc_metrics(plot: dict, spec: SpiceInput) -> dict:
    """Extract the operating point; currents come from the actual resistor drops."""
    vb = float(_channel(plot, "v(vin)")[0].real)
    vc = float(_channel(plot, "v(vc)")[0].real)
    ve = float(_channel(plot, "v(ve)")[0].real)
    vout = float(_channel(plot, "v(vout)")[0].real)
    ic = (spec.vcc - vc) / spec.rc
    ie = ve / spec.re
    return {
        "vb": vb, "ve": ve, "vc": vc, "vout": vout, "vce": vc - ve,
        "ic": ic, "ie": ie, "ib": ie - ic,
    }


def ac_metrics(plot: dict) -> dict:
    """Gain is |Vout/Vin| at the handout's vin/vout nodes, phase in degrees."""
    frequencies = [abs(complex(point[0]).real) for point in plot["points"]]
    vin = _channel(plot, "v(vin)")
    vout = _channel(plot, "v(vout)")
    points = []
    for frequency, input_ph, output_ph in zip(frequencies, vin, vout):
        ratio = complex(output_ph) / complex(input_ph)
        points.append({
            "frequency": frequency,
            "gain": abs(ratio),
            "gain_db": 20.0 * math.log10(abs(ratio)) if ratio else float("-inf"),
            "phase_deg": _wrap_degrees(math.degrees(cmath.phase(ratio))),
        })
    peak = max(points, key=lambda point: point["gain"])
    threshold = peak["gain"] / math.sqrt(2.0)
    above = [point for point in points if point["gain"] >= threshold]
    low = min(above, key=lambda point: point["frequency"])
    high = max(above, key=lambda point: point["frequency"])
    return {
        "points": points,
        "midband_gain": peak["gain"],
        "midband_gain_db": peak["gain_db"],
        "midband_freq": peak["frequency"],
        "phase_deg": peak["phase_deg"],
        "fl_hz": NOT_DETERMINED if low["frequency"] == frequencies[0] else low["frequency"],
        "fh_hz": NOT_DETERMINED if high["frequency"] == frequencies[-1] else high["frequency"],
    }


def transient_metrics(plot: dict, frequency: float) -> dict:
    """Measure peak amplitudes and phase at the fundamental from real samples."""
    times = [float(value) for value in _channel(plot, "time")]
    vin = [float(value) for value in _channel(plot, "v(vin)")]
    vout = [float(value) for value in _channel(plot, "v(vout)")]
    period = 1.0 / frequency
    points = []
    for time, input_v, output_v in zip(times, vin, vout):
        points.append({"time": time, "vin": input_v, "vout": output_v})

    # Use the last two cycles only: the first cycles contain the solver's
    # start-up transient and would otherwise corrupt the phase measurement.
    window_start = times[-1] - 2.0 * period
    indices = [i for i, t in enumerate(times) if t >= window_start]
    if len(indices) < 4:
        indices = list(range(len(times)))
    stable_times = [times[i] for i in indices]
    stable_vin = [vin[i] for i in indices]
    stable_vout = [vout[i] for i in indices]

    def ac_part(values: list[float]) -> list[float]:
        mean = sum(values) / len(values)
        return [value - mean for value in values]

    def angle(values: list[float]) -> float:
        centred = ac_part(values)
        sine = sum(v * math.sin(2 * math.pi * t / period) for t, v in zip(stable_times, centred))
        cosine = sum(v * math.cos(2 * math.pi * t / period) for t, v in zip(stable_times, centred))
        return math.degrees(math.atan2(cosine, sine))

    vin_peak = (max(stable_vin) - min(stable_vin)) / 2.0
    vout_peak = (max(stable_vout) - min(stable_vout)) / 2.0
    return {
        "points": points,
        "period": period,
        "vin_peak": vin_peak,
        "vout_peak": vout_peak,
        "gain": vout_peak / vin_peak if vin_peak else 0.0,
        "phase_deg": _wrap_degrees(angle(stable_vout) - angle(stable_vin)),
    }


def run_simulation(spec: SpiceInput, executable: str | None = None, timeout: int = 30) -> SpiceResult:
    """Run one real ngspice batch job and return parsed results or raise SpiceError."""
    exe = executable or find_ngspice()
    if not exe or not (Path(exe).is_file() or shutil.which(exe)):
        raise SpiceError("ngspice ไม่พบใน PATH — กรุณาตั้ง NGSPICE_EXECUTABLE หรือติดตั้ง ngspice")
    netlist = build_netlist(spec)
    engine = _engine_version(exe)
    with tempfile.TemporaryDirectory(prefix="lab04_ngspice_") as directory:
        work = Path(directory)
        (work / "circuit.cir").write_text(netlist, encoding="utf-8")
        command = [str(exe), "-b", "-o", "run.log", "-r", "run.raw", "circuit.cir"]
        try:
            completed = subprocess.run(
                command, cwd=work, capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            raise SpiceError(f"ngspice timeout หลัง {timeout} วินาที") from exc
        except OSError as exc:
            raise SpiceError(f"เรียก ngspice ไม่ได้: {exc}") from exc

        log = (work / "run.log").read_text(encoding="utf-8", errors="replace") if (work / "run.log").exists() else ""
        combined = "\n".join([completed.stdout or "", completed.stderr or "", log])
        failure = re.search(r"(?im)^error:|run simulation\(s\) aborted|fatal error", combined)
        if completed.returncode != 0 or failure:
            detail = failure.group(0) if failure else f"return code {completed.returncode}"
            raise SpiceError(f"ngspice run failed: {detail}\n{combined[-800:]}")
        raw_path = work / "run.raw"
        if not raw_path.exists() or raw_path.stat().st_size == 0:
            raise SpiceError("ngspice ไม่ได้เขียนไฟล์ผล (run.raw ว่างหรือไม่มี)")
        raw_text = raw_path.read_text(encoding="utf-8", errors="replace")
        plots = parse_raw(raw_text)
        expected = {"dc": "Operating Point", "ac": "AC Analysis",
                    "transient": "Transient Analysis"}[spec.analysis]
        if expected not in plots or not plots[expected]["points"]:
            raise SpiceError(f"ngspice ไม่มีผล {expected} ในไฟล์ที่เขียนออกมา")

        if spec.analysis == "dc":
            values = dc_metrics(plots[expected], spec)
        elif spec.analysis == "ac":
            values = ac_metrics(plots[expected])
        else:
            values = transient_metrics(plots[expected], spec.frequency)
        excerpt = "\n".join(line for line in combined.splitlines() if line.strip())[-1200:]
        return SpiceResult(
            analysis=spec.analysis, status="Success", engine=engine, model=MODEL_NAME,
            netlist=netlist, values=values, log_excerpt=excerpt,
        )
