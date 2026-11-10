import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dc_bias import (BiasInput, calculate_dc_bias, REGION_ACTIVE,
                     REGION_CUTOFF, REGION_SATURATION)


class TestReferenceOperatingPoint(unittest.TestCase):
    def setUp(self):
        # ค่าตัวอย่างจาก handout Lab 02
        self.inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                             rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)

    def test_reference_operating_point(self):
        r = calculate_dc_bias(self.inp)
        self.assertAlmostEqual(r.vth, 2.163934, places=6)
        self.assertAlmostEqual(r.rth, 18_032.786885, places=4)
        self.assertAlmostEqual(r.ib, 12.298581e-6, places=12)
        self.assertAlmostEqual(r.ic, 1.2298581e-3, places=9)
        self.assertAlmostEqual(r.ie, 1.2421567e-3, places=9)
        self.assertAlmostEqual(r.ve, 1.2421567, places=6)
        self.assertAlmostEqual(r.vb, 1.9421567, places=6)
        self.assertAlmostEqual(r.vc, 9.2943122, places=6)
        self.assertAlmostEqual(r.vce, 8.0521555, places=6)
        self.assertEqual(r.region, REGION_ACTIVE)

    def test_kvl_consistency(self):
        r = calculate_dc_bias(self.inp)
        self.assertAlmostEqual(r.ic * self.inp.rc + r.vce + r.ie * self.inp.re,
                               self.inp.vcc, places=9)


class TestRegionDetection(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        # VTH = 12*1000/101000 = 0.1188 V < 0.7 V
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=1_000.0,
                        rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        r = calculate_dc_bias(inp)
        self.assertEqual(r.region, REGION_CUTOFF)
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertAlmostEqual(r.ve, 0.0, places=9)
        self.assertAlmostEqual(r.vb, 0.1188119, places=6)
        self.assertAlmostEqual(r.vc, 12.0, places=9)
        self.assertAlmostEqual(r.vce, 12.0, places=9)
        self.assertTrue(r.warnings)

    def test_saturation_warning_when_vce_low(self):
        # RC = 10k => VC = 12 - 12.2986 = -0.2986 V, VCE = -1.54 V
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                        rc=10_000.0, re=1_000.0, beta=100.0, vbe=0.70)
        r = calculate_dc_bias(inp)
        self.assertEqual(r.region, REGION_SATURATION)
        self.assertLess(r.vce, 0.3)
        self.assertTrue(r.warnings)
        # ยังรายงานค่าดิบตามสมการ ไม่ clamp
        self.assertAlmostEqual(r.ic, 1.2298581e-3, places=9)

    def test_active_has_no_warning(self):
        inp = BiasInput(vcc=12.0, r1=100_000.0, r2=22_000.0,
                        rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(calculate_dc_bias(inp).warnings, [])
