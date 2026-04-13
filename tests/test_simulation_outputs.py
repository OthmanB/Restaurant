import unittest

import numpy as np

from sources.config_loader import (
    load_menu_config,
    load_behavior_config,
    load_population_config,
    load_expenses_config,
)
from sources.simulation_api import simulate_year


from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / 'setup'


def load_reference_configs():
    menu = load_menu_config(str(SETUP / 'menu_setup_R1.yaml'))
    behavior = load_behavior_config(str(SETUP / 'behavior_setup_r1.yaml'))
    population = load_population_config(str(SETUP / 'population_setup_R1.yaml'))
    expenses = load_expenses_config(str(SETUP / 'expenses_setup_R1.yaml'))
    return menu, behavior, population, expenses


class TestSimulationOutputs(unittest.TestCase):
    def test_simulate_year_structure(self):
        menu, behavior, population, expenses = load_reference_configs()
        result = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=1)

        for key in ('metadata', 'time', 'population', 'revenue', 'expenses', 'income'):
            self.assertIn(key, result)

        self.assertEqual(len(result['income']['month']), 12)
        self.assertIn('config_hash', result['metadata'])
        self.assertIn('rng_kind', result['metadata'])

    def test_deterministic_reproducibility_same_seed(self):
        menu, behavior, population, expenses = load_reference_configs()
        a = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=7)
        b = simulate_year(menu, behavior, population, expenses, mode='deterministic', seed=7)

        self.assertTrue(np.allclose(a['income']['month'], b['income']['month']))
        self.assertEqual(a['metadata']['config_hash'], b['metadata']['config_hash'])


if __name__ == '__main__':
    unittest.main()
