import json
import warnings
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


class ConfigValidationError(ValueError):
    pass


_JSON_DEPRECATION_WARNED = False


def _as_path(path_like):
    return Path(path_like)


def _load_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError as exc:
        raise ConfigValidationError(f"Config file not found: {path}") from exc


def _parse_config(path):
    text = _load_text(path)
    suffix = path.suffix.lower()

    if suffix == '.json':
        global _JSON_DEPRECATION_WARNED
        if not _JSON_DEPRECATION_WARNED:
            warnings.warn(
                f"JSON config format is deprecated for {path}. Prefer YAML (.yaml/.yml).",
                DeprecationWarning,
                stacklevel=2,
            )
            _JSON_DEPRECATION_WARNED = True
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(f"Invalid JSON syntax in {path}: {exc}") from exc

    if suffix in ('.yaml', '.yml'):
        if yaml is None:
            raise ConfigValidationError(
                f"YAML file provided ({path}) but PyYAML is not installed. Install pyyaml or use JSON."
            )
        try:
            data = yaml.safe_load(text)
        except Exception as exc:  # yaml parser raises multiple subclasses
            raise ConfigValidationError(f"Invalid YAML syntax in {path}: {exc}") from exc
        if data is None:
            raise ConfigValidationError(f"YAML file {path} is empty")
        return data

    raise ConfigValidationError(
        f"Unsupported config extension for {path}. Expected .json, .yaml, or .yml"
    )


def _require_dict(name, obj):
    if not isinstance(obj, dict):
        raise ConfigValidationError(f"{name} must be a mapping/dict")


def _require_key(obj, key, ctx):
    if key not in obj:
        raise ConfigValidationError(f"Missing required key '{key}' in {ctx}")


def _require_number(value, ctx, min_value=None, max_value=None):
    if not isinstance(value, (int, float)):
        raise ConfigValidationError(f"{ctx} must be numeric, got {type(value).__name__}")
    if min_value is not None and value < min_value:
        raise ConfigValidationError(f"{ctx} must be >= {min_value}, got {value}")
    if max_value is not None and value > max_value:
        raise ConfigValidationError(f"{ctx} must be <= {max_value}, got {value}")


def _require_bool(value, ctx):
    if not isinstance(value, bool):
        raise ConfigValidationError(f"{ctx} must be a boolean")


def _normalize_expenses_aliases(expenses):
    # recurring.recuring_period -> recurring.recurring_period
    recurring = expenses.get('recurring')
    if isinstance(recurring, dict):
        if 'recuring_period' in recurring and 'recurring_period' not in recurring:
            recurring['recurring_period'] = recurring.pop('recuring_period')

    # payment_fees.method.*.payement_proba -> payment_proba
    payment_fees = expenses.get('payment_fees')
    if isinstance(payment_fees, dict):
        methods = payment_fees.get('method')
        if isinstance(methods, dict):
            for m in methods.values():
                if isinstance(m, dict) and 'payement_proba' in m and 'payment_proba' not in m:
                    m['payment_proba'] = m.pop('payement_proba')

    return expenses


def validate_menu_config(menu):
    _require_dict('menu_setup', menu)
    for key in ('unit', 'limit_by_service', 'service_list', 'service_time', 'menu_items'):
        _require_key(menu, key, 'menu_setup')

    _require_bool(menu['limit_by_service'], "menu_setup['limit_by_service']")

    service_list = menu['service_list']
    service_time = menu['service_time']
    menu_items = menu['menu_items']

    if not isinstance(service_list, list) or len(service_list) == 0:
        raise ConfigValidationError("menu_setup['service_list'] must be a non-empty list")
    if not isinstance(service_time, list) or len(service_time) != len(service_list):
        raise ConfigValidationError(
            "menu_setup['service_time'] must be a list with same length as service_list"
        )
    for i, interval in enumerate(service_time):
        if not isinstance(interval, list) or len(interval) != 2:
            raise ConfigValidationError(f"menu_setup['service_time'][{i}] must be [start, end]")
        _require_number(interval[0], f"menu_setup['service_time'][{i}][0]", 0, 24)
        _require_number(interval[1], f"menu_setup['service_time'][{i}][1]", 0, 24)
        if interval[0] >= interval[1]:
            raise ConfigValidationError(
                f"menu_setup['service_time'][{i}] start must be < end, got {interval}"
            )

    if not isinstance(menu_items, dict) or len(menu_items) == 0:
        raise ConfigValidationError("menu_setup['menu_items'] must be a non-empty mapping")

    for item_name, item in menu_items.items():
        if not isinstance(item, dict):
            raise ConfigValidationError(f"menu_setup['menu_items']['{item_name}'] must be mapping")
        for key in ('service', 'price', 'cost', 'daily_proba'):
            _require_key(item, key, f"menu_setup['menu_items']['{item_name}']")
        if item['service'] not in service_list:
            raise ConfigValidationError(
                f"menu item '{item_name}' service='{item['service']}' not in service_list={service_list}"
            )
        _require_number(item['price'], f"menu item '{item_name}' price", 0)
        _require_number(item['cost'], f"menu item '{item_name}' cost", 0)
        _require_number(item['daily_proba'], f"menu item '{item_name}' daily_proba", 0, 1)

    return menu


def validate_behavior_config(behavior):
    _require_dict('behavior_setup', behavior)
    for key in ('model_resolution', 'yearly_function', 'reference', 'restaurant'):
        _require_key(behavior, key, 'behavior_setup')

    _require_number(behavior['model_resolution'], "behavior_setup['model_resolution']", 0)

    yearly = behavior['yearly_function']
    _require_dict("behavior_setup['yearly_function']", yearly)
    for key in ('func', 'params'):
        _require_key(yearly, key, "behavior_setup['yearly_function']")
    if yearly['func'] != 'default':
        raise ConfigValidationError("behavior_setup['yearly_function']['func'] must be 'default'")
    if not isinstance(yearly['params'], list) or len(yearly['params']) != 4:
        raise ConfigValidationError("behavior_setup['yearly_function']['params'] must be a list of length 4")
    for i, p in enumerate(yearly['params']):
        _require_number(p, f"behavior_setup['yearly_function']['params'][{i}]")

    reference = behavior['reference']
    restaurant = behavior['restaurant']
    _require_dict("behavior_setup['reference']", reference)
    _require_dict("behavior_setup['restaurant']", restaurant)

    expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in expected_days:
        _require_key(reference, day, "behavior_setup['reference']")
        _require_key(restaurant, day, "behavior_setup['restaurant']")

        ref_day = reference[day]
        rest_day = restaurant[day]
        _require_dict(f"behavior_setup['reference']['{day}']", ref_day)
        _require_dict(f"behavior_setup['restaurant']['{day}']", rest_day)

        for key in ('working_hours', 'daily_distributions'):
            _require_key(ref_day, key, f"behavior_setup['reference']['{day}']")
        _require_key(rest_day, 'working_hours', f"behavior_setup['restaurant']['{day}']")

        for ctx, work in (
            (f"behavior_setup['reference']['{day}']['working_hours']", ref_day['working_hours']),
            (f"behavior_setup['restaurant']['{day}']['working_hours']", rest_day['working_hours']),
        ):
            if not isinstance(work, list) or len(work) != 2:
                raise ConfigValidationError(f"{ctx} must be [start, end]")
            _require_number(work[0], f"{ctx}[0]", 0, 24)
            _require_number(work[1], f"{ctx}[1]", 0, 24)
            if work[0] >= work[1]:
                raise ConfigValidationError(f"{ctx} start must be < end")

        daily = ref_day['daily_distributions']
        if not isinstance(daily, list) or len(daily) == 0:
            raise ConfigValidationError(
                f"behavior_setup['reference']['{day}']['daily_distributions'] must be non-empty list"
            )
        for i, comp in enumerate(daily):
            if not isinstance(comp, list) or len(comp) != 3:
                raise ConfigValidationError(
                    f"behavior_setup['reference']['{day}']['daily_distributions'][{i}] must have 3 values"
                )
            _require_number(comp[0], f"daily_distributions[{i}][0]", 0)
            _require_number(comp[1], f"daily_distributions[{i}][1]", 0, 24)
            _require_number(comp[2], f"daily_distributions[{i}][2]", 0)

    return behavior


def validate_population_config(pop):
    _require_dict('population_setup', pop)
    for key in ('attractiveness', 'Nliving', 'Ntransit', 'Nworking'):
        _require_key(pop, key, 'population_setup')

    attractiveness = pop['attractiveness']
    _require_dict("population_setup['attractiveness']", attractiveness)
    for key in ('nr', 'Nvisits_per_day'):
        _require_key(attractiveness, key, "population_setup['attractiveness']")
    _require_number(attractiveness['nr'], "population_setup['attractiveness']['nr']", 0)
    _require_number(attractiveness['Nvisits_per_day'], "population_setup['attractiveness']['Nvisits_per_day']", 0)

    nliving = pop['Nliving']
    _require_dict("population_setup['Nliving']", nliving)
    for key in ('population_density', 'effective_time_radius', 'travel_speed'):
        _require_key(nliving, key, "population_setup['Nliving']")
        _require_number(nliving[key], f"population_setup['Nliving']['{key}']", 0)

    ntransit = pop['Ntransit']
    _require_dict("population_setup['Ntransit']", ntransit)
    _require_key(ntransit, 'Ntransit', "population_setup['Ntransit']")
    _require_number(ntransit['Ntransit'], "population_setup['Ntransit']['Ntransit']", 0)

    nworking = pop['Nworking']
    _require_dict("population_setup['Nworking']", nworking)
    _require_key(nworking, 'places', "population_setup['Nworking']")
    places = nworking['places']
    if not isinstance(places, dict) or len(places) == 0:
        raise ConfigValidationError("population_setup['Nworking']['places'] must be non-empty mapping")

    for place_key, place in places.items():
        _require_dict(f"population_setup['Nworking']['places']['{place_key}']", place)
        for key in ('distance', 'Nworkers', 'Commute_fraction'):
            _require_key(place, key, f"population_setup['Nworking']['places']['{place_key}']")
        _require_number(place['distance'], f"place '{place_key}' distance", 0)
        _require_number(place['Nworkers'], f"place '{place_key}' Nworkers", 0)
        _require_number(place['Commute_fraction'], f"place '{place_key}' Commute_fraction", 0, 1)

    return pop


def validate_expenses_config(expenses):
    _require_dict('expenses_setup', expenses)
    expenses = _normalize_expenses_aliases(expenses)

    for key in ('payment_fees', 'staff', 'recurring'):
        _require_key(expenses, key, 'expenses_setup')

    payment_fees = expenses['payment_fees']
    _require_dict("expenses_setup['payment_fees']", payment_fees)
    _require_key(payment_fees, 'method', "expenses_setup['payment_fees']")
    methods = payment_fees['method']
    if not isinstance(methods, dict) or len(methods) == 0:
        raise ConfigValidationError("expenses_setup['payment_fees']['method'] must be non-empty mapping")

    proba_sum = 0.0
    for method_name, method in methods.items():
        _require_dict(f"payment method '{method_name}'", method)
        for key in ('fees', 'payment_proba'):
            _require_key(method, key, f"payment method '{method_name}'")
        _require_number(method['fees'], f"payment method '{method_name}' fees", 0)
        _require_number(method['payment_proba'], f"payment method '{method_name}' payment_proba", 0, 1)
        proba_sum += method['payment_proba']
    if abs(proba_sum - 1.0) > 1e-8:
        raise ConfigValidationError(
            f"expenses_setup payment method probabilities must sum to 1.0; got {proba_sum:.8f}"
        )

    staff = expenses['staff']
    _require_dict("expenses_setup['staff']", staff)
    _require_key(staff, 'staff_list', "expenses_setup['staff']")
    staff_list = staff['staff_list']
    if not isinstance(staff_list, dict) or len(staff_list) == 0:
        raise ConfigValidationError("expenses_setup['staff']['staff_list'] must be non-empty mapping")
    expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for staff_name, profile in staff_list.items():
        _require_dict(f"staff '{staff_name}'", profile)
        for key in ('hourly_rate', 'working_hours'):
            _require_key(profile, key, f"staff '{staff_name}'")
        _require_number(profile['hourly_rate'], f"staff '{staff_name}' hourly_rate", 0)
        work = profile['working_hours']
        _require_dict(f"staff '{staff_name}' working_hours", work)
        for day in expected_days:
            _require_key(work, day, f"staff '{staff_name}' working_hours")
            intervals = work[day]
            if not isinstance(intervals, list):
                raise ConfigValidationError(
                    f"staff '{staff_name}' working_hours['{day}'] must be a list of intervals"
                )
            for idx, interval in enumerate(intervals):
                if interval == []:
                    continue
                if not isinstance(interval, list) or len(interval) != 2:
                    raise ConfigValidationError(
                        f"staff '{staff_name}' working_hours['{day}'][{idx}] must be [start, end]"
                    )
                _require_number(interval[0], f"staff '{staff_name}' interval start", 0, 24)
                _require_number(interval[1], f"staff '{staff_name}' interval end", 0, 24)
                if interval[0] >= interval[1]:
                    raise ConfigValidationError(
                        f"staff '{staff_name}' interval start must be < end for day '{day}'"
                    )

    recurring = expenses['recurring']
    _require_dict("expenses_setup['recurring']", recurring)
    _require_key(recurring, 'recurring_list', "expenses_setup['recurring']")
    recurring_list = recurring['recurring_list']
    if not isinstance(recurring_list, dict) or len(recurring_list) == 0:
        raise ConfigValidationError("expenses_setup['recurring']['recurring_list'] must be non-empty mapping")
    for name, value in recurring_list.items():
        _require_number(value, f"expenses_setup recurring item '{name}'", 0)

    if 'recurring_period' in recurring:
        if recurring['recurring_period'] not in ('day', 'week', 'month', 'year'):
            raise ConfigValidationError(
                "expenses_setup['recurring']['recurring_period'] must be one of day/week/month/year"
            )

    if 'loss_fraction' in expenses and isinstance(expenses['loss_fraction'], (int, float)):
        _require_number(expenses['loss_fraction'], "expenses_setup['loss_fraction']", 0, 1)

    return expenses


def load_menu_config(path_like):
    path = _as_path(path_like)
    cfg = _parse_config(path)
    return validate_menu_config(cfg)


def load_behavior_config(path_like):
    path = _as_path(path_like)
    cfg = _parse_config(path)
    return validate_behavior_config(cfg)


def load_population_config(path_like):
    path = _as_path(path_like)
    cfg = _parse_config(path)
    return validate_population_config(cfg)


def load_expenses_config(path_like):
    path = _as_path(path_like)
    cfg = _parse_config(path)
    return validate_expenses_config(cfg)
