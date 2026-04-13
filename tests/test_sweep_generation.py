import unittest

from sources.config_loader import (
    load_menu_config,
    load_behavior_config,
    load_population_config,
    load_expenses_config,
)
from sources.simulation_api import simulate_batch, expand_sweep_configs, SweepSpecError


from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / 'setup'


def load_reference_configs():
    menu = load_menu_config(str(SETUP / 'menu_setup_R1.yaml'))
    behavior = load_behavior_config(str(SETUP / 'behavior_setup_r1.yaml'))
    population = load_population_config(str(SETUP / 'population_setup_R1.yaml'))
    expenses = load_expenses_config(str(SETUP / 'expenses_setup_R1.yaml'))
    return menu, behavior, population, expenses


class TestSweepGeneration(unittest.TestCase):
    def test_expand_sweep_configs(self):
        menu, behavior, population, expenses = load_reference_configs()
        base = {
            'menu_cfg': menu,
            'behavior_cfg': behavior,
            'population_cfg': population,
            'expenses_cfg': expenses,
        }
        sweep = {
            'population_cfg.attractiveness.nr': [10, 20],
            'menu_cfg.limit_by_service': [True],
        }
        variants = expand_sweep_configs(base, sweep, sweep_id='intent-sweep')
        self.assertEqual(len(variants), 2)
        self.assertEqual(variants[0]['sweep_id'], 'intent-sweep')

    def test_expand_sweep_invalid_path(self):
        menu, behavior, population, expenses = load_reference_configs()
        base = {
            'menu_cfg': menu,
            'behavior_cfg': behavior,
            'population_cfg': population,
            'expenses_cfg': expenses,
        }
        with self.assertRaises(SweepSpecError):
            expand_sweep_configs(base, {'population_cfg.invalid.path': [1]}, sweep_id='bad')

    def test_simulate_batch_metadata(self):
        menu, behavior, population, expenses = load_reference_configs()
        base = {
            'menu_cfg': menu,
            'behavior_cfg': behavior,
            'population_cfg': population,
            'expenses_cfg': expenses,
        }
        variants = expand_sweep_configs(base, {'population_cfg.attractiveness.nr': [20]}, sweep_id='batch-meta')
        batch = simulate_batch(variants, seed=3, n_runs=1, mode='deterministic')

        self.assertEqual(len(batch), 1)
        metadata = batch[0]['metadata']
        self.assertIn('batch_run_index', metadata)
        self.assertIn('batch_sweep_index', metadata)
        self.assertEqual(metadata['sweep_id'], 'batch-meta')


if __name__ == '__main__':
    unittest.main()
