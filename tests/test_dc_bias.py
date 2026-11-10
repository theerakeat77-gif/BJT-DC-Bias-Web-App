import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dc_bias import BiasInput, calculate_dc_bias, REGION_ACTIVE


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
