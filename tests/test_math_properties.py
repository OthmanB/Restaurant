import unittest

import numpy as np

from sources.functions_population import (
    A_fct,
    Influence_fct,
    Nliving,
    manyGauss_fct,
    Norm_manyGauss_fct,
    daily_base_fct,
    yearly_modulation,
)


class TestMathematicalProperties(unittest.TestCase):
    def test_attractiveness_monotonicity(self):
        nr = np.arange(0, 30)
        vals = np.asarray([A_fct(int(n)) for n in nr], dtype=float)
        self.assertTrue(np.all(vals > 0))
        self.assertTrue(np.all(np.diff(vals) < 0))
        self.assertAlmostEqual(vals[0], 1.0)

    def test_influence_radial_decay(self):
        reff = 0.8
        r = np.linspace(0, 3 * reff, 200)
        influence = Influence_fct(r, reff)
        self.assertAlmostEqual(float(influence[0]), 1.0, places=8)
        self.assertTrue(np.all(influence >= 0))
        self.assertTrue(np.all(np.diff(influence) <= 1e-12))

    def test_nliving_scales_with_radius_squared(self):
        rho = 442.0
        reff = 0.9
        n1 = Nliving(rho, reff)
        n2 = Nliving(rho, 2 * reff)
        self.assertAlmostEqual(n2 / n1, 4.0, places=8)

    def test_manygauss_integrability_and_nonnegativity(self):
        params = [[0.3, 8.0, 0.6], [0.4, 12.0, 1.0], [0.5, 18.0, 0.8]]
        norm = Norm_manyGauss_fct(params, x_truncate=[7, 21], range_int=[0, 24])
        self.assertGreater(norm, 0)

        x = np.linspace(0, 24, 400)
        y = manyGauss_fct(x, params, x_truncate=[7, 21])
        self.assertTrue(np.all(y >= 0))

    def test_daily_base_is_normalized_when_requested(self):
        params = [[0.3, 8.0, 0.6], [0.4, 12.0, 1.0], [0.5, 18.0, 0.8]]
        x = np.linspace(0, 24, 1200)
        y = daily_base_fct(x, params, normalise=True, working_hours=[7, 21])
        area = np.trapezoid(y, x)
        self.assertAlmostEqual(area, 1.0, places=3)

    def test_daily_base_truncation_limit_condition(self):
        params = [[0.5, 8.0, 0.5], [0.5, 12.0, 0.6], [0.2, 18.0, 0.9]]
        x = np.linspace(0, 24, 240)
        y = daily_base_fct(x, params, normalise=False, working_hours=[7, 21])
        outside = np.where(np.logical_or(x < 7, x > 21))[0]
        self.assertTrue(np.allclose(y[outside], 0.0, atol=1e-12))

    def test_yearly_modulation_bounds(self):
        setup = {
            'yearly_function': {
                'func': 'default',
                'params': [1.0, 0.2, 1.0, 0.0],
            }
        }
        t = np.linspace(0, 365 * 24, 3000)
        _, y = yearly_modulation(setup, t, unit='hour')
        self.assertGreaterEqual(np.min(y), 0.8 - 1e-6)
        self.assertLessEqual(np.max(y), 1.2 + 1e-6)


if __name__ == '__main__':
    unittest.main()
