import unittest
import warnings
from pathlib import Path

from sources.config_loader import (
    load_menu_config,
    load_behavior_config,
    load_population_config,
    load_expenses_config,
    validate_menu_config,
)


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / 'setup'


class TestConfigLoading(unittest.TestCase):
    def test_reference_configs_load(self):
        menu = load_menu_config(str(SETUP / 'menu_setup_R1.yaml'))
        behavior = load_behavior_config(str(SETUP / 'behavior_setup_r1.yaml'))
        population = load_population_config(str(SETUP / 'population_setup_R1.yaml'))
        expenses = load_expenses_config(str(SETUP / 'expenses_setup_R1.yaml'))

        self.assertIn('menu_items', menu)
        self.assertIn('reference', behavior)
        self.assertIn('Nliving', population)
        self.assertIn('payment_fees', expenses)

    def test_legacy_json_still_loads(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            menu = load_menu_config(str(SETUP / 'menu_setup_R1.json'))
        self.assertIn('menu_items', menu)

    def test_alias_normalization_expenses(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            expenses = load_expenses_config(str(SETUP / 'expenses_setup_R1.json'))
        self.assertIn('payment_proba', expenses['payment_fees']['method']['cash'])
        self.assertIn('recurring_period', expenses['recurring'])

    def test_invalid_menu_rejected(self):
        menu = load_menu_config(str(SETUP / 'menu_setup_R1.yaml'))
        menu_bad = dict(menu)
        menu_bad['service_time'] = [[7, 11]]
        with self.assertRaises(Exception):
            validate_menu_config(menu_bad)


if __name__ == '__main__':
    unittest.main()
