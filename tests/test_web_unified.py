import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spice_engine
from app import app

BASE_FORM = {
    "vcc": "12", "r1": "100k", "r2": "22k", "rc": "2.2k", "re": "1k",
    "beta": "100", "vbe": "0.70", "rb": "", "rl": "10k", "cin": "10u",
    "cout": "10u", "amplitude": "0.01", "frequency": "1k",
}


def fake_result(analysis="dc"):
    values = {
        "vb": 1.98, "ve": 1.33, "vc": 9.09, "vce": 7.76,
        "ic": 0.001321, "ie": 0.001331, "ib": 0.00001,
        "midband_gain_db": 4.87, "midband_freq": 5012.0, "phase_deg": -179.9,
        "fl_hz": 1.41, "fh_hz": spice_engine.NOT_DETERMINED,
        "vin_peak": 0.01, "vout_peak": 0.0175, "gain": 1.75, "period": 0.001,
        "points": [
            {"time": 0.0, "vin": 0.0, "vout": 0.0,
             "frequency": 1.0, "gain": 1.0, "gain_db": 0.0, "phase_deg": 180.0},
            {"time": 0.0005, "vin": 0.01, "vout": -0.0175,
             "frequency": 1000.0, "gain": 1.75, "gain_db": 4.87, "phase_deg": -180.0},
            {"time": 0.001, "vin": 0.0, "vout": 0.0,
             "frequency": 1e6, "gain": 1.0, "gain_db": 0.0, "phase_deg": 180.0},
        ],
    }
    return spice_engine.SpiceResult(
        analysis=analysis, status="Success", engine="ngspice-47",
        model="t2n2222", netlist="* fake netlist",
        values=values, log_excerpt="fake log", warnings=[],
    )


class TestUnifiedForm(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_has_exactly_one_select_with_all_modes(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertEqual(body.count("<select"), 1)
        for value in ("divider", "fixed", "emitter", "ce-dc", "ce-ac", "ce-tran"):
            self.assertIn(f'value="{value}"', body)
        self.assertNotIn('name="analysis"', body)

    def test_run_divider_uses_analytical_bias(self):
        response = self.client.post("/run", data={**BASE_FORM, "mode": "divider"})
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("1.942", body)
        self.assertIn("ACTIVE", body)
        self.assertNotIn('class="status success"', body)

    def test_run_ce_dc_uses_spice_solver(self):
        with patch.object(spice_engine, "run_simulation", return_value=fake_result()) as run:
            response = self.client.post("/run", data={**BASE_FORM, "mode": "ce-dc"})
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('class="status success"', body)
        self.assertIn("ngspice-47", body)
        self.assertEqual(run.call_args.args[0].analysis, "dc")

    def test_run_ce_ac_sets_ac_analysis(self):
        with patch.object(spice_engine, "run_simulation", return_value=fake_result("ac")) as run:
            response = self.client.post("/run", data={**BASE_FORM, "mode": "ce-ac"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(run.call_args.args[0].analysis, "ac")
        self.assertIn("AC Frequency Response", response.get_data(as_text=True))

    def test_run_ce_transient_sets_transient_analysis(self):
        result = fake_result("transient")
        with patch.object(spice_engine, "run_simulation", return_value=result) as run:
            response = self.client.post("/run", data={**BASE_FORM, "mode": "ce-tran"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(run.call_args.args[0].analysis, "transient")
        self.assertIn("Transient Response", response.get_data(as_text=True))

    def test_invalid_mode_reports_error_without_success(self):
        with patch.object(spice_engine, "run_simulation") as run:
            response = self.client.post("/run", data={**BASE_FORM, "mode": "bogus"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="errors"', body)
        self.assertNotIn('class="status success"', body)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
