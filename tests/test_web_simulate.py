import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spice_engine
from app import app

SIM_FORM = {
    "vcc": "12", "r1": "100k", "r2": "22k", "rc": "2.2k", "re": "1k",
    "rl": "10k", "cin": "10u", "cout": "10u", "amplitude": "0.01",
    "frequency": "1k", "analysis": "dc",
}


def fake_result(analysis="dc", values=None):
    return spice_engine.SpiceResult(
        analysis=analysis,
        status="Success",
        engine="ngspice-47",
        model="t2n2222",
        netlist="* netlist from real run",
        values=values or {"vb": 1.98, "ve": 1.33, "vc": 9.09, "vce": 7.76,
                          "ic": 0.00132, "ie": 0.00133, "ib": 0.00001},
        log_excerpt="Total analysis time (seconds) = 0.01",
        warnings=[],
    )


class TestSimulateRoute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_simulation_page_shows_spice_provenance(self):
        with patch.object(spice_engine, "run_simulation", return_value=fake_result()) as run:
            response = self.client.post("/simulate", data=SIM_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("ngspice-47", body)
        self.assertIn("t2n2222", body)
        self.assertIn("SPICE", body)
        self.assertIn("Analytical", body)
        self.assertIn("1.98", body)
        run.assert_called_once()

    def test_invalid_re_shows_error_without_success(self):
        with patch.object(spice_engine, "run_simulation") as run:
            response = self.client.post("/simulate", data={**SIM_FORM, "re": "0"})
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Error", body)
        self.assertNotIn('class="status success"', body)
        run.assert_not_called()

    def test_engine_error_is_shown_and_no_fake_success(self):
        with patch.object(spice_engine, "run_simulation", side_effect=spice_engine.SpiceError("solver not found")):
            response = self.client.post("/simulate", data=SIM_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("solver not found", body)
        self.assertNotIn('class="status success"', body)

    def test_analytical_route_still_works(self):
        response = self.client.post("/calculate", data={
            "mode": "divider", "vcc": "12", "r1": "100k", "r2": "22k",
            "rc": "2.2k", "re": "1k", "beta": "100", "vbe": "0.70", "rb": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("1.942", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
