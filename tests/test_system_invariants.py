import unittest
from pathlib import Path

import numpy as np

from sources.config_loader import (
    load_menu_config,
    load_behavior_config,
    load_population_config,
    load_expenses_config,
)
from sources.simulation_api import simulate_year


def _load_reference_configs():
    root = Path(__file__).resolve().parents[1]
    setup = root / 'setup'
    menu = load_menu_config(str(setup / 'menu_setup_R1.yaml'))
    behavior = load_behavior_config(str(setup / 'behavior_setup_r1.yaml'))
    population = load_population_config(str(setup / 'population_setup_R1.yaml'))
    expenses = load_expenses_config(str(setup / 'expenses_setup_R1.yaml'))
    return menu, behavior, population, expenses


class TestSystemInvariants(unittest.TestCase):
    def test_non_negative_population_and_flows(self):
        menu, behavior, population, expenses = _load_reference_configs()
        r = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=10)

        self.assertTrue(np.all(np.asarray(r['population']['Nc_hours']) >= 0))
        self.assertTrue(np.all(np.asarray(r['population']['Nc_day']) >= 0))
        self.assertTrue(np.all(np.asarray(r['revenue']['day']) >= 0))
        self.assertTrue(np.all(np.asarray(r['expenses']['total_day']) >= 0))

    def test_income_identity_revenue_minus_expenses(self):
        menu, behavior, population, expenses = _load_reference_configs()
        r = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=10)

        self.assertTrue(np.allclose(
            np.asarray(r['income']['day']),
            np.asarray(r['revenue']['day']) - np.asarray(r['expenses']['total_day'])
        ))
        self.assertTrue(np.allclose(
            np.asarray(r['income']['week']),
            np.asarray(r['revenue']['week']) - np.asarray(r['expenses']['total_week'])
        ))
        self.assertTrue(np.allclose(
            np.asarray(r['income']['month']),
            np.asarray(r['revenue']['month']) - np.asarray(r['expenses']['total_month'])
        ))

    def test_output_time_monotonicity(self):
        menu, behavior, population, expenses = _load_reference_configs()
        r = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=11)

        for key in ('hours', 'day', 'week', 'month'):
            t = np.asarray(r['time'][key], dtype=float)
            self.assertTrue(np.all(np.diff(t) >= 0))

    def test_config_hash_stability_same_input(self):
        menu, behavior, population, expenses = _load_reference_configs()
        a = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=1)
        b = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=999)
        self.assertEqual(a['metadata']['config_hash'], b['metadata']['config_hash'])

    def test_stochastic_fee_reproducibility_same_seed(self):
        menu, behavior, population, expenses = _load_reference_configs()
        a = simulate_year(menu, behavior, population, expenses, mode='stochastic', seed=42)
        b = simulate_year(menu, behavior, population, expenses, mode='stochastic', seed=42)
        self.assertTrue(np.allclose(
            np.asarray(a['expenses']['fees_day']),
            np.asarray(b['expenses']['fees_day'])
        ))

    def test_stochastic_fee_differs_for_different_seed(self):
        menu, behavior, population, expenses = _load_reference_configs()
        # Retry a few seeds to avoid rare accidental equality when a single method dominates.
        found_difference = False
        for s1, s2 in ((42, 43), (101, 202), (7, 99)):
            a = simulate_year(menu, behavior, population, expenses, mode='stochastic', seed=s1)
            b = simulate_year(menu, behavior, population, expenses, mode='stochastic', seed=s2)
            if not np.allclose(np.asarray(a['expenses']['fees_day']), np.asarray(b['expenses']['fees_day'])):
                found_difference = True
                break
        self.assertTrue(found_difference)


if __name__ == '__main__':
    unittest.main()
