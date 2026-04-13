"""
Manual visual probes and ad-hoc experimentation helpers.

This file is intentionally NOT part of the automated test suite.
Automated tests now live under /tests with intent-based modules.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import simpson

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency for manual helpers
    yaml = None
from functions_population import daily_base_fct, weekly_fct, yearly_fct, compute_Nc
from misc import combinations, rem_duplicates, deep_rem_duplicates


def _load_raw_setup(path_like):
    path = Path(path_like)
    text = path.read_text(encoding='utf-8')
    suffix = path.suffix.lower()
    if suffix == '.json':
        return json.loads(text)
    if suffix in ('.yaml', '.yml'):
        if yaml is None:
            raise RuntimeError('PyYAML is required to read YAML setup files in manual helpers')
        data = yaml.safe_load(text)
        if data is None:
            raise RuntimeError(f'YAML setup file is empty: {path}')
        return data
    raise RuntimeError(f'Unsupported setup extension for {path}; expected .json, .yaml, or .yml')



def show_daily_profile():
    hour = np.linspace(0, 24, 200)
    params = [[0.3, 7, 0.5], [0.5, 12, 1], [0.2, 18, 1]]
    f = daily_base_fct(hour, params, normalise=False)
    plt.plot(hour, f)
    plt.title('Daily base function (manual visual check)')
    plt.show()


def show_weekly_profile(test_setup_file='setup/tests/behavior_setup_test.yaml'):
    setup = _load_raw_setup(test_setup_file)
    time_h, afluence_h = weekly_fct(setup)
    plt.plot(time_h / 24.0, afluence_h)
    plt.title('Weekly function (manual visual check)')
    plt.show()


def show_yearly_profile(test_setup_file='setup/tests/behavior_setup_test.yaml'):
    setup = _load_raw_setup(test_setup_file)
    time_h, afluence_h = yearly_fct(setup)
    plt.plot(time_h / 24.0, afluence_h)
    plt.title('Yearly function (manual visual check)')
    plt.show()


def show_compute_nc(test_behavior_setup_file='setup/tests/behavior_setup_test.yaml',
                    test_population_setup_file='setup/tests/population_setup_test.yaml'):
    behavior_setup = _load_raw_setup(test_behavior_setup_file)
    population_setup = _load_raw_setup(test_population_setup_file)
    time, nc_weekday, nc_weekend = compute_Nc(behavior_setup, population_setup)
    plt.plot(time / 24.0, nc_weekday, label='weekday')
    plt.plot(time / 24.0, nc_weekend, label='weekend')
    plt.legend()
    plt.title('Nc profile (manual visual check)')
    plt.show()


def inspect_combinations():
    names = ["Bacon", "Eggs", "Bread", "Donuts"]
    proba = [0.5, 0.5, 0.5, 0.5]
    price = [10, 5, 5, 5]
    cost = [3, 1, 1, 1]

    vec = [[names[i], proba[i], price[i], cost[i]] for i in range(len(names))]
    combi_all = combinations(vec, without_recurence=True)
    combi_unique = deep_rem_duplicates(combi_all)

    revenues = []
    for c in combi_unique:
        p_joint = 1
        p_paid = 0
        for cc in c:
            p_joint *= cc[1]
            p_paid += cc[2]
        revenues.append(p_joint * p_paid)

    print('Unique combinations:', len(combi_unique))
    print('Total expected revenue contribution:', np.sum(revenues))


if __name__ == '__main__':
    # Manual script entrypoint only.
    show_daily_profile()
