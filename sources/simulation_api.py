import hashlib
import json
from copy import deepcopy
from itertools import product

import numpy as np

from error_checks import check_time_is_1y
from functions_population import compute_Nc
from functions_income import (
    daily_revenue_and_cost_menu_items_perclient,
    daily_revenues_expenses_menuitem,
    expenses_fees,
    expenses_staff,
    expenses_recurent,
)
from misc import integrate, sums


class SweepSpecError(ValueError):
    pass


def _compute_month_names():
    return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _compute_day_names():
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _build_rng(seed):
    if seed is None:
        return np.random.default_rng()
    return np.random.default_rng(int(seed))



def _stable_hash_payload(payload):
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _build_config_fingerprint(menu_setup, behavior_setup, population_setup, expenses_setup):
    return _stable_hash_payload(
        {
            'menu': menu_setup,
            'behavior': behavior_setup,
            'population': population_setup,
            'expenses': expenses_setup,
        }
    )


def _expected_fee_factor(expenses_setup):
    methods = expenses_setup['payment_fees']['method']
    factor = 0.0
    for method_name, method_cfg in methods.items():
        payment_proba = method_cfg.get('payment_proba', method_cfg.get('payement_proba'))
        if payment_proba is None:
            raise ValueError(f"Missing payment probability for method {method_name!r}")
        factor += payment_proba * method_cfg['fees']
    return factor


def _compute_time_blocks(time_hours, Nc_hours, Nc_weekday_hours, Nc_weekend_hours, month_in_days):
    Dt = 24
    time_day_Nc, Nc_day = integrate(time_hours, Nc_hours, Dt)
    time_day_Nc_weekday, Nc_day_weekday = integrate(time_hours, Nc_weekday_hours, Dt)
    time_day_Nc_weekend, Nc_day_weekend = integrate(time_hours, Nc_weekend_hours, Dt)

    time_day_Nc = time_day_Nc[:-1]
    time_day_Nc_weekday = time_day_Nc_weekday[:-1]
    time_day_Nc_weekend = time_day_Nc_weekend[:-1]
    Nc_day = Nc_day[:-1]
    Nc_day_weekday = Nc_day_weekday[:-1]
    Nc_day_weekend = Nc_day_weekend[:-1]

    Dt = 7
    time_week_Nc, Nc_week = integrate(time_day_Nc, Nc_day, Dt)

    Dt = month_in_days
    time_month_Nc, Nc_month = integrate(time_day_Nc, Nc_day, Dt)

    return {
        'time_day_Nc': time_day_Nc,
        'time_day_Nc_weekday': time_day_Nc_weekday,
        'time_day_Nc_weekend': time_day_Nc_weekend,
        'Nc_day': Nc_day,
        'Nc_day_weekday': Nc_day_weekday,
        'Nc_day_weekend': Nc_day_weekend,
        'Nc_week': Nc_week,
        'Nc_month': Nc_month,
        'time_week_Nc': time_week_Nc,
        'time_month_Nc': time_month_Nc,
    }


def _compute_revenue_expense_blocks(
    menu_setup,
    behavior_setup,
    expenses_setup,
    time_day,
    Nc_day,
    Nc_week,
    Nc_month,
    month_in_days,
    mode,
    rng,
):
    daily_work_hours = (
        behavior_setup['restaurant']['Monday']['working_hours'][1]
        - behavior_setup['restaurant']['Monday']['working_hours'][0]
    )

    R, E, Services, avail_services = daily_revenue_and_cost_menu_items_perclient(menu_setup)
    R_menu_day, E_menu_day = daily_revenues_expenses_menuitem(
        menu_setup, R, E, Services, avail_services, time_day, Nc_day, daily_work_hours
    )

    Dt = 7
    time_week, R_menu_week = sums(time_day, R_menu_day, Dt)
    time_week, E_menu_week = sums(time_day, E_menu_day, Dt)

    Dt = month_in_days
    time_month, R_menu_month = sums(time_day, R_menu_day, Dt)
    time_month, E_menu_month = sums(time_day, E_menu_day, Dt)

    if mode == 'deterministic':
        fee_factor = _expected_fee_factor(expenses_setup)
        E_fees_day = np.asarray(R_menu_day, dtype=float) * fee_factor
        E_fees_week = np.asarray(R_menu_week, dtype=float) * fee_factor
        E_fees_month = np.asarray(R_menu_month, dtype=float) * fee_factor
    else:
        E_fees_day = expenses_fees(expenses_setup, R_menu_day, Nc_day, rng=rng)
        E_fees_week = expenses_fees(expenses_setup, R_menu_week, Nc_week, rng=rng)
        E_fees_month = expenses_fees(expenses_setup, R_menu_month, Nc_month, rng=rng)

    E_staff_day = 0
    E_staff_week = 0
    E_staff_month = 0
    for staff in expenses_setup['staff']['staff_list']:
        E_staff_day += expenses_staff(expenses_setup, staff, period=1)
        E_staff_week += expenses_staff(expenses_setup, staff, period=7)
        E_staff_month += expenses_staff(expenses_setup, staff, period=month_in_days)

    E_rec_day = expenses_recurent(expenses_setup, period=1)
    E_rec_week = expenses_recurent(expenses_setup, period=7)
    E_rec_month = expenses_recurent(expenses_setup)

    E_tot_day = E_menu_day + E_staff_day + E_rec_day + E_fees_day
    E_tot_week = E_menu_week + E_staff_week + E_rec_week + E_fees_week
    E_tot_month = E_menu_month + E_staff_month + E_rec_month + E_fees_month

    return {
        'R_menu_day': R_menu_day,
        'E_menu_day': E_menu_day,
        'time_week': time_week,
        'R_menu_week': R_menu_week,
        'E_menu_week': E_menu_week,
        'time_month': time_month,
        'R_menu_month': R_menu_month,
        'E_menu_month': E_menu_month,
        'E_fees_day': E_fees_day,
        'E_fees_week': E_fees_week,
        'E_fees_month': E_fees_month,
        'E_staff_day': E_staff_day,
        'E_staff_week': E_staff_week,
        'E_staff_month': E_staff_month,
        'E_rec_day': E_rec_day,
        'E_rec_week': E_rec_week,
        'E_rec_month': E_rec_month,
        'E_tot_day': E_tot_day,
        'E_tot_week': E_tot_week,
        'E_tot_month': E_tot_month,
    }


def simulate_year(
    menu_cfg,
    behavior_cfg,
    population_cfg,
    expenses_cfg,
    *,
    seed=None,
    mode='deterministic',
    run_id=None,
    sweep_id=None,
    sweep_params=None,
):
    if mode not in ('deterministic', 'stochastic'):
        raise ValueError("simulate_year(): mode must be 'deterministic' or 'stochastic'")

    month_in_days = 30.41666666666

    menu_setup = deepcopy(menu_cfg)
    behavior_setup = deepcopy(behavior_cfg)
    population_setup = deepcopy(population_cfg)
    expenses_setup = deepcopy(expenses_cfg)

    rng = _build_rng(seed)

    time_hours, Nc_weekday_hours, Nc_weekend_hours = compute_Nc(behavior_setup, population_setup)

    err_codes_0 = check_time_is_1y(time_hours, y=Nc_weekday_hours)
    if err_codes_0[0] is not False:
        raise ValueError(f"Invalid Nc_weekday_hours yearly span: {err_codes_0}")

    err_codes_1 = check_time_is_1y(time_hours, y=Nc_weekend_hours)
    if err_codes_1[0] is not False:
        raise ValueError(f"Invalid Nc_weekend_hours yearly span: {err_codes_1}")

    Nc_hours = Nc_weekday_hours + Nc_weekend_hours

    time_blocks = _compute_time_blocks(
        time_hours,
        Nc_hours,
        Nc_weekday_hours,
        Nc_weekend_hours,
        month_in_days,
    )

    revenue_expense_blocks = _compute_revenue_expense_blocks(
        menu_setup,
        behavior_setup,
        expenses_setup,
        time_blocks['time_day_Nc'],
        time_blocks['Nc_day'],
        time_blocks['Nc_week'],
        time_blocks['Nc_month'],
        month_in_days,
        mode,
        rng,
    )

    I_day = revenue_expense_blocks['R_menu_day'] - revenue_expense_blocks['E_tot_day']
    I_week = revenue_expense_blocks['R_menu_week'] - revenue_expense_blocks['E_tot_week']
    I_month = revenue_expense_blocks['R_menu_month'] - revenue_expense_blocks['E_tot_month']

    config_hash = _build_config_fingerprint(menu_setup, behavior_setup, population_setup, expenses_setup)

    return {
        'metadata': {
            'mode': mode,
            'seed': seed,
            'run_id': run_id,
            'sweep_id': sweep_id,
            'sweep_params': deepcopy(sweep_params) if sweep_params is not None else None,
            'config_hash': config_hash,
            'model_version': 'phase4.1',
            'rng_kind': str(type(rng.bit_generator).__name__),
            'rng_state_hash': _stable_hash_payload(rng.bit_generator.state),
            'month_in_days': month_in_days,
            'day_names': _compute_day_names(),
            'month_names': _compute_month_names(),
            'unit': menu_setup['unit'],
        },
        'time': {
            'hours': time_hours,
            'day': time_blocks['time_day_Nc'],
            'day_weekday': time_blocks['time_day_Nc_weekday'],
            'day_weekend': time_blocks['time_day_Nc_weekend'],
            'week': time_blocks['time_week_Nc'],
            'month': time_blocks['time_month_Nc'],
            'week_integrated': revenue_expense_blocks['time_week'],
            'month_integrated': revenue_expense_blocks['time_month'],
        },
        'population': {
            'Nc_hours': Nc_hours,
            'Nc_weekday_hours': Nc_weekday_hours,
            'Nc_weekend_hours': Nc_weekend_hours,
            'Nc_day': time_blocks['Nc_day'],
            'Nc_day_weekday': time_blocks['Nc_day_weekday'],
            'Nc_day_weekend': time_blocks['Nc_day_weekend'],
            'Nc_week': time_blocks['Nc_week'],
            'Nc_month': time_blocks['Nc_month'],
        },
        'revenue': {
            'day': revenue_expense_blocks['R_menu_day'],
            'week': revenue_expense_blocks['R_menu_week'],
            'month': revenue_expense_blocks['R_menu_month'],
        },
        'expenses': {
            'menu_day': revenue_expense_blocks['E_menu_day'],
            'menu_week': revenue_expense_blocks['E_menu_week'],
            'menu_month': revenue_expense_blocks['E_menu_month'],
            'fees_day': revenue_expense_blocks['E_fees_day'],
            'fees_week': revenue_expense_blocks['E_fees_week'],
            'fees_month': revenue_expense_blocks['E_fees_month'],
            'staff_day': revenue_expense_blocks['E_staff_day'],
            'staff_week': revenue_expense_blocks['E_staff_week'],
            'staff_month': revenue_expense_blocks['E_staff_month'],
            'recurring_day': revenue_expense_blocks['E_rec_day'],
            'recurring_week': revenue_expense_blocks['E_rec_week'],
            'recurring_month': revenue_expense_blocks['E_rec_month'],
            'total_day': revenue_expense_blocks['E_tot_day'],
            'total_week': revenue_expense_blocks['E_tot_week'],
            'total_month': revenue_expense_blocks['E_tot_month'],
        },
        'income': {
            'day': I_day,
            'week': I_week,
            'month': I_month,
        },
    }


def simulate_batch(config_iterable, *, seed=None, n_runs=1, mode='deterministic'):
    if n_runs < 1:
        raise ValueError('simulate_batch(): n_runs must be >= 1')

    results = []
    run_index = 0
    for cfg in config_iterable:
        for _ in range(n_runs):
            run_seed = None if seed is None else int(seed) + run_index
            result = simulate_year(
                cfg['menu_cfg'],
                cfg['behavior_cfg'],
                cfg['population_cfg'],
                cfg['expenses_cfg'],
                seed=run_seed,
                mode=mode,
                run_id=f'run-{run_index}',
                sweep_id=cfg.get('sweep_id'),
                sweep_params=cfg.get('sweep_params'),
            )
            result['metadata']['batch_run_index'] = run_index
            result['metadata']['batch_base_seed'] = seed
            result['metadata']['batch_n_runs'] = n_runs
            result['metadata']['batch_sweep_index'] = cfg.get('sweep_index')
            results.append(result)
            run_index += 1
    return results


def _set_nested_value(target, dotted_path, value):
    parts = dotted_path.split('.')
    cursor = target
    for key in parts[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            raise SweepSpecError(f"Sweep path '{dotted_path}' invalid at '{key}'")
        cursor = cursor[key]
    leaf = parts[-1]
    if leaf not in cursor:
        raise SweepSpecError(f"Sweep path '{dotted_path}' missing leaf '{leaf}'")
    cursor[leaf] = value


def expand_sweep_configs(base_configs, sweep_spec, *, sweep_id='sweep-0'):
    required = {'menu_cfg', 'behavior_cfg', 'population_cfg', 'expenses_cfg'}
    if set(base_configs.keys()) != required:
        raise SweepSpecError(f"base_configs must have keys {sorted(required)}")

    if not isinstance(sweep_spec, dict) or len(sweep_spec) == 0:
        raise SweepSpecError('sweep_spec must be a non-empty mapping')

    sweep_keys = list(sweep_spec.keys())
    sweep_values = []
    for key in sweep_keys:
        values = sweep_spec[key]
        if not isinstance(values, list) or len(values) == 0:
            raise SweepSpecError(f"Sweep values for '{key}' must be non-empty list")
        sweep_values.append(values)

    variants = []
    for idx, combo in enumerate(product(*sweep_values)):
        cfg = {
            'menu_cfg': deepcopy(base_configs['menu_cfg']),
            'behavior_cfg': deepcopy(base_configs['behavior_cfg']),
            'population_cfg': deepcopy(base_configs['population_cfg']),
            'expenses_cfg': deepcopy(base_configs['expenses_cfg']),
        }
        params = {}
        for k, v in zip(sweep_keys, combo):
            root, dotted = k.split('.', 1)
            if root not in cfg:
                raise SweepSpecError(f"Sweep root '{root}' not in base configs")
            _set_nested_value(cfg[root], dotted, v)
            params[k] = v

        cfg['sweep_id'] = sweep_id
        cfg['sweep_params'] = params
        cfg['sweep_index'] = idx
        variants.append(cfg)

    return variants
