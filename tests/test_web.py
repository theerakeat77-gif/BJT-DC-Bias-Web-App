import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import collect_inputs, parse_float, parse_resistance


class TestParseResistance(unittest.TestCase):
    def test_plain_ohms(self):
        self.assertEqual(parse_resistance("100000"), 100_000.0)

    def test_kilo_lowercase(self):
        self.assertEqual(parse_resistance("100k"), 100_000.0)

    def test_kilo_uppercase_and_decimal(self):
        self.assertEqual(parse_resistance("2.2K"), 2_200.0)

    def test_mega(self):
        self.assertEqual(parse_resistance("1M"), 1_000_000.0)

    def test_whitespace_trimmed(self):
        self.assertEqual(parse_resistance("  100k  "), 100_000.0)

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_resistance("abc")

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            parse_resistance("-100k")


class TestCollectInputs(unittest.TestCase):
    def valid_form(self):
        return {"vcc": "12", "r1": "100k", "r2": "22k", "rc": "2.2k",
                "re": "1k", "beta": "100", "vbe": "0.70"}

    def test_valid_form_returns_bias_input(self):
        inp, errors = collect_inputs(self.valid_form())
        self.assertEqual(errors, [])
        self.assertEqual(inp.r1, 100_000.0)
        self.assertEqual(inp.beta, 100.0)

    def test_missing_field_reports_error(self):
        form = self.valid_form()
        del form["vcc"]
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("VCC" in e for e in errors))

    def test_zero_resistance_reports_error_not_division_by_zero(self):
        form = self.valid_form()
        form["r2"] = "0"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("R2" in e for e in errors))

    def test_non_numeric_reports_error(self):
        form = self.valid_form()
        form["rc"] = "abc"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("RC" in e for e in errors))

    def test_negative_beta_reports_error(self):
        form = self.valid_form()
        form["beta"] = "-5"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("β" in e or "beta" in e for e in errors))

    def test_vbe_not_below_vcc_reports_error(self):
        form = self.valid_form()
        form["vbe"] = "12"
        inp, errors = collect_inputs(form)
        self.assertIsNone(inp)
        self.assertTrue(any("VBE" in e for e in errors))

    def test_empty_form_reports_all_seven_fields(self):
        inp, errors = collect_inputs({})
        self.assertIsNone(inp)
        self.assertEqual(len(errors), 7)
