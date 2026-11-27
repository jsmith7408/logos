import unittest
from admission31 import admit

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(loss_per_byte=2., latency_ms=10., regressions=0)
        self.good = dict(loss_per_byte=1.8, latency_ms=11., regressions=0)
    def test_improvement(self):
        self.assertEqual(admit(self.base, self.good), (True, ()))
    def test_equal(self):
        self.assertFalse(admit(self.base, self.base)[0])
    def test_regression(self):
        self.assertFalse(admit(self.base, dict(self.good, regressions=1))[0])
    def test_latency(self):
        self.assertFalse(admit(self.base, dict(self.good, latency_ms=13))[0])
    def test_invalid(self):
        for x in (float('nan'), float('inf'), -1, True):
            with self.assertRaises(ValueError):
                admit(self.base, dict(self.good, loss_per_byte=x))
    def test_boundary(self):
        self.assertTrue(admit(self.base, dict(self.good, latency_ms=12))[0])
    def test_baseline_failure(self):
        self.assertFalse(admit(dict(self.base, regressions=1), self.good)[0])
