import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spice_engine import (
    SpiceError,
    SpiceInput,
    ac_metrics,
    build_netlist,
    dc_metrics,
    find_ngspice,
    parse_raw,
    run_simulation,
    transient_metrics,
    validate_spice_input,
)


BASE_FORM = {
    "vcc": "12",
    "r1": "100k",
    "r2": "22k",
    "rc": "2.2k",
    "re": "1k",
    "rl": "10k",
    "cin": "10u",
    "cout": "10u",
    "amplitude": "0.01",
    "frequency": "1k",
    "analysis": "dc",
}

RAW_SAMPLE = """Title: test
Date: Tue Nov 24 17:00:00  2026
Plotname: Operating Point
Flags: real
No. Variables: 4
No. Points: 1
Variables:
\t0\tv(vin)\tvoltage
\t1\tv(vc)\tvoltage
\t2\tv(vout)\tvoltage
\t3\tv(ve)\tvoltage
Values:
0\t\t1.5
\t9.0
\t0.0
\t0.8
Title: test
Plotname: AC Analysis
Flags: complex
No. Variables: 3
No. Points: 3
Variables:
\t0\tfrequency\tfrequency
\t1\tv(vin)\tvoltage
\t2\tv(vout)\tvoltage
Values:
0\t\t1.0,0.0
\t0.01,0.0
\t-0.1,0.0
1\t\t100.0,0.0
\t0.01,0.0
\t-1.0,0.0
2\t\t10000.0,0.0
\t0.01,0.0
\t-0.1,0.0
Title: test
Plotname: Transient Analysis
Flags: real
No. Variables: 3
No. Points: 4
Variables:
\t0\ttime\ttime
\t1\tv(vin)\tvoltage
\t2\tv(vout)\tvoltage
Values:
0\t\t0.0
\t0.0
\t0.0
1\t\t0.25
\t0.01
\t-0.01
2\t\t0.5
\t0.0
\t0.0
3\t\t0.75
\t-0.01
\t0.01
"""


class TestValidateSpiceInput(unittest.TestCase):
    def test_baseline_form_is_valid(self):
        spec, errors = validate_spice_input(BASE_FORM)
        self.assertEqual(errors, [])
        self.assertAlmostEqual(spec.vcc, 12.0)
        self.assertAlmostEqual(spec.r1, 100_000.0)
        self.assertAlmostEqual(spec.re, 1_000.0)
        self.assertAlmostEqual(spec.cin, 10e-6)
        self.assertAlmostEqual(spec.amplitude, 0.01)
        self.assertAlmostEqual(spec.frequency, 1_000.0)

    def test_re_zero_is_rejected(self):
        spec, errors = validate_spice_input({**BASE_FORM, "re": "0"})
        self.assertIsNone(spec)
        self.assertTrue(errors)

    def test_bad_amplitude_is_rejected_before_netlist(self):
        spec, errors = validate_spice_input({**BASE_FORM, "amplitude": "1;rm -rf /"})
        self.assertIsNone(spec)
        self.assertTrue(errors)

    def test_unknown_analysis_is_rejected(self):
        spec, errors = validate_spice_input({**BASE_FORM, "analysis": "fft"})
        self.assertIsNone(spec)
        self.assertTrue(errors)


class TestBuildNetlist(unittest.TestCase):
    def setUp(self):
        self.spec, _ = validate_spice_input(BASE_FORM)

    def test_analysis_directive_matches_selection(self):
        self.assertIn(".op", build_netlist(self.spec))
        ac = build_netlist(SpiceInput(**{**self.spec.__dict__, "analysis": "ac"}))
        self.assertIn(".ac dec", ac)
        self.assertNotIn(".op", ac)
        tran = build_netlist(SpiceInput(**{**self.spec.__dict__, "analysis": "transient"}))
        self.assertIn(".tran", tran)

    def test_reference_nodes_and_model_are_present(self):
        netlist = build_netlist(self.spec)
        for token in ("R1 vcc vin", "R2 vin 0", "RC vcc vc", "RE ve 0", "RL vout 0",
                      "Q1 vc vin ve", "CIN src vin", "COUT vc vout", ".model t2n2222 npn"):
            self.assertIn(token, netlist)
        self.assertIn("1k", netlist)
        self.assertIn("10u", netlist)

    def test_frequency_changes_transient_card(self):
        slow = build_netlist(SpiceInput(**{**self.spec.__dict__, "analysis": "transient", "frequency": 1_000.0}))
        fast = build_netlist(SpiceInput(**{**self.spec.__dict__, "analysis": "transient", "frequency": 10_000.0}))
        self.assertNotEqual(slow, fast)


class TestParseRaw(unittest.TestCase):
    def test_all_three_plots_are_parsed(self):
        plots = parse_raw(RAW_SAMPLE)
        self.assertEqual(set(plots), {"Operating Point", "AC Analysis", "Transient Analysis"})
        op = plots["Operating Point"]
        self.assertEqual(op["variables"], ["v(vin)", "v(vc)", "v(vout)", "v(ve)"])
        self.assertEqual(op["points"][0], [1.5, 9.0, 0.0, 0.8])

    def test_complex_ac_values_are_complex(self):
        ac = parse_raw(RAW_SAMPLE)["AC Analysis"]
        self.assertEqual(ac["points"][1][0], 100.0)
        self.assertEqual(ac["points"][1][2], complex(-1.0, 0.0))


class TestMetrics(unittest.TestCase):
    def test_dc_metrics_derive_currents_from_resistors(self):
        spec, _ = validate_spice_input(BASE_FORM)
        plots = parse_raw(RAW_SAMPLE)
        result = dc_metrics(plots["Operating Point"], spec)
        self.assertAlmostEqual(result["vb"], 1.5)
        self.assertAlmostEqual(result["vc"], 9.0)
        self.assertAlmostEqual(result["vce"], 8.2)
        self.assertAlmostEqual(result["ic"] * 1e3, (12.0 - 9.0) / 2200 * 1e3)
        self.assertAlmostEqual(result["ie"] * 1e3, 0.8)

    def test_ac_metrics_gain_phase_and_cutoff(self):
        plots = parse_raw(RAW_SAMPLE)
        result = ac_metrics(plots["AC Analysis"])
        self.assertAlmostEqual(result["midband_gain"], 100.0)
        self.assertAlmostEqual(result["midband_freq"], 100.0)
        self.assertAlmostEqual(abs(result["phase_deg"]), 180.0, delta=1e-6)
        self.assertAlmostEqual(result["fl_hz"], 100.0)
        self.assertAlmostEqual(result["fh_hz"], 100.0)

    def test_ac_missing_crossover_is_reported_not_invented(self):
        # Gain is largest at the first (lowest) sweep point: no lower -3 dB
        # crossing exists inside this sweep, so fL must not be invented.
        plot = {
            "variables": ["frequency", "v(vin)", "v(vout)"],
            "points": [
                [1.0, complex(0.01, 0), complex(-1.0, 0)],
                [100.0, complex(0.01, 0), complex(-0.01, 0)],
                [10000.0, complex(0.01, 0), complex(-0.001, 0)],
            ],
        }
        result = ac_metrics(plot)
        self.assertEqual(result["fl_hz"], "not determined in sweep range")

    def test_transient_metrics_amplitude_and_inverted_phase(self):
        result = transient_metrics(parse_raw(RAW_SAMPLE)["Transient Analysis"], 1.0)
        self.assertAlmostEqual(result["vin_peak"], 0.01)
        self.assertAlmostEqual(result["vout_peak"], 0.01)
        self.assertAlmostEqual(abs(result["phase_deg"]), 180.0, delta=1e-6)


class TestRealEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = find_ngspice()
        if cls.exe is None:
            raise unittest.SkipTest("ngspice executable not found in this environment")

    def test_real_dc_run_and_re_direction(self):
        spec, errors = validate_spice_input({**BASE_FORM, "analysis": "dc"})
        self.assertEqual(errors, [])
        base = run_simulation(spec, executable=self.exe, timeout=30)
        self.assertEqual(base.status, "Success")
        self.assertIn("ngspice", base.engine)
        self.assertEqual(base.model, "t2n2222")
        self.assertGreater(base.values["ic"], 0)
        self.assertGreater(base.values["vce"], 0)

        bigger, _ = validate_spice_input({**BASE_FORM, "analysis": "dc", "re": "2k"})
        high_re = run_simulation(bigger, executable=self.exe, timeout=30)
        self.assertEqual(high_re.status, "Success")
        self.assertLess(high_re.values["ic"], base.values["ic"])
        self.assertGreater(high_re.values["vce"], base.values["vce"])

    def test_real_ac_and_transient_have_series_from_run(self):
        ac_spec, _ = validate_spice_input({**BASE_FORM, "analysis": "ac"})
        ac = run_simulation(ac_spec, executable=self.exe, timeout=30)
        self.assertEqual(ac.status, "Success")
        self.assertGreater(len(ac.values["points"]), 20)
        self.assertTrue(all(math.isfinite(p["gain_db"]) for p in ac.values["points"]))

        tran_spec, _ = validate_spice_input({**BASE_FORM, "analysis": "transient"})
        tran = run_simulation(tran_spec, executable=self.exe, timeout=30)
        self.assertEqual(tran.status, "Success")
        self.assertGreater(len(tran.values["points"]), 100)
        loud, _ = validate_spice_input({**BASE_FORM, "analysis": "transient", "amplitude": "0.02"})
        louder = run_simulation(loud, executable=self.exe, timeout=30)
        self.assertGreater(louder.values["vin_peak"], tran.values["vin_peak"] * 1.5)

    def test_missing_executable_raises_spice_error(self):
        spec, _ = validate_spice_input(BASE_FORM)
        with self.assertRaises(SpiceError):
            run_simulation(spec, executable="C:/definitely/not/ngspice.exe", timeout=5)


if __name__ == "__main__":
    unittest.main()
