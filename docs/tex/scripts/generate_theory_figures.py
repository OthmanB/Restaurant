import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['mathtext.fontset'] = 'dejavuserif'
plt.rcParams['font.family'] = 'DejaVu Serif'

ROOT = Path(__file__).resolve().parents[1]
GRAPHICS = ROOT / 'graphics'
PARAMS_PATH = Path(__file__).with_name('theory_figure_params.json')
MANIFEST_PATH = Path(__file__).with_name('figure_manifest.json')


def gaussian(x, mu, sigma):
    return np.exp(-((x - mu) ** 2) / (2.0 * sigma ** 2))


def normalized_gaussian_sum(x, peaks, integral_target=1.0):
    y = np.zeros_like(x, dtype=float)
    for amp, mu, sigma in peaks:
        y += amp * gaussian(x, mu, sigma)
    area = np.trapezoid(y, x)
    if area > 0:
        y = y * (integral_target / area)
    return y


def week_weight_series(hours, weights):
    day_index = np.floor(hours / 24.0).astype(int) % 7
    weights = np.asarray(weights, dtype=float)
    weights = weights / np.mean(weights)
    return weights[day_index]


def yearly_envelope(days, yearly):
    base = yearly['base']
    depth = yearly['depth']
    phase = yearly['phase']
    return base - depth * np.cos(2.0 * np.pi * days / 365.0 + phase)


def service_profiles(hours):
    services = {
        'breakfast': normalized_gaussian_sum(hours, [(1.0, 8.0, 0.9)], 1.0),
        'lunch': normalized_gaussian_sum(hours, [(1.0, 13.0, 1.1)], 1.0),
        'dinner': normalized_gaussian_sum(hours, [(1.0, 19.0, 1.2)], 1.0),
    }
    return services


def expected_spend_curves(hours, items):
    profiles = service_profiles(hours)
    spend = np.zeros_like(hours)
    prod_cost = np.zeros_like(hours)
    per_item = {}
    for item in items:
        profile = profiles[item['service']]
        revenue_curve = item['price'] * item['daily_proba'] * profile
        cost_curve = item['cost'] * item['daily_proba'] * profile
        spend += revenue_curve
        prod_cost += cost_curve
        per_item[item['name']] = {
            'revenue_curve': revenue_curve,
            'cost_curve': cost_curve,
            'service': item['service'],
        }
    return spend, prod_cost, per_item


def fee_factor(methods):
    return sum(method['proba'] * method['fee'] for method in methods)


def product(values):
    result = 1.0
    for value in values:
        result *= value
    return result


def richer_population(cfg, include_transit=False):
    reff = cfg['effective_time_radius_min'] * cfg['travel_speed_kmh'] / 60.0
    nliving = 2.0 * np.pi * reff ** 2 * cfg['rho']
    nworking = 0.0
    for site in cfg['work_sites']:
        overlap = site['population'] * site['overlap_fraction']
        influence = np.exp(-(site['distance_km'] ** 2) / (2.0 * reff ** 2))
        nworking += (site['population'] - overlap) * influence
    ntransit = cfg['transit_fraction'] * nliving if include_transit else 0.0
    return reff, nliving, nworking, ntransit


def monthly_totals(times_hours, revenue_rate, total_cost_rate):
    day_index = np.floor(times_hours / 24.0).astype(int)
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    months = []
    start = 0
    for length in month_lengths:
        end = start + length
        mask = (day_index >= start) & (day_index < end)
        months.append((np.trapezoid(revenue_rate[mask], times_hours[mask]), np.trapezoid(total_cost_rate[mask], times_hours[mask])))
        start = end
    return months


def save(fig, stem, conceptual=False):
    png_path = GRAPHICS / f'{stem}.png'
    fig.savefig(png_path, dpi=220, bbox_inches='tight')
    outputs = [str(png_path.relative_to(ROOT))]
    if conceptual:
        svg_path = GRAPHICS / f'{stem}.svg'
        fig.savefig(svg_path, bbox_inches='tight')
        outputs.append(str(svg_path.relative_to(ROOT)))
    plt.close(fig)
    return outputs


def make_population_schematic(cfg):
    reff, nliving, nworking, _ = richer_population(cfg)
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    theta = np.linspace(0, 2.0 * np.pi, 400)
    ax.plot(reff * np.cos(theta), reff * np.sin(theta), color='tab:blue', label='Effective reach')
    ax.scatter([0.0], [0.0], color='crimson', s=70, label='Restaurant')
    for idx, site in enumerate(cfg['work_sites']):
        ax.scatter([site['distance_km']], [0.25 * (-1) ** idx], color='tab:green', s=60)
        ax.text(site['distance_km'] + 0.03, 0.25 * (-1) ** idx, f'Site {idx + 1}')
    ax.text(-reff * 0.95, reff * 0.85, rf'$N_l \approx {nliving:.0f}$')
    ax.text(-reff * 0.95, reff * 0.65, rf'$N_w \approx {nworking:.0f}$')
    ax.set_xlabel('Distance east-west [km]')
    ax.set_ylabel('Distance north-south [km]')
    ax.set_title('Population-reservoir schematic')
    ax.set_aspect('equal', adjustable='box')
    ax.grid(alpha=0.2)
    ax.legend(loc='upper right')
    return save(fig, 'fig_population_schematic', conceptual=True)


def make_kernel_comparison(cfg):
    reff, _, _, _ = richer_population(cfg)
    r = np.linspace(0.0, 2.5 * reff, 400)
    gaussian_kernel = np.exp(-(r ** 2) / (2.0 * reff ** 2))
    exponential_kernel = np.exp(-r / reff)
    hard_cutoff = (r <= reff).astype(float)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(r, gaussian_kernel, label='Gaussian reference', linewidth=2.2)
    ax.plot(r, exponential_kernel, label='Exponential', linewidth=2.0)
    ax.plot(r, hard_cutoff, label='Hard cutoff', linewidth=2.0)
    ax.set_xlabel('Distance [km]')
    ax.set_ylabel('Kernel value')
    ax.set_title('Influence-kernel comparison')
    ax.grid(alpha=0.25)
    ax.legend()
    return save(fig, 'fig_kernel_comparison', conceptual=True)


def make_timescale_decomposition(cfg):
    hours = np.linspace(0.0, 24.0, 400)
    days = np.linspace(0.0, 365.0, 365)
    daily = normalized_gaussian_sum(hours, cfg['daily_peaks'], cfg['nu'])
    weekly = np.asarray(cfg['week_weights'], dtype=float)
    weekly = weekly / np.mean(weekly)
    yearly = yearly_envelope(days, cfg['yearly'])
    fig, axs = plt.subplots(2, 2, figsize=(8.5, 6.0))
    axs[0, 0].plot(hours, daily, color='tab:blue')
    axs[0, 0].set_title(r'Daily kernel $D(\tau_d)$')
    axs[0, 1].bar(np.arange(7), weekly, color='tab:orange')
    axs[0, 1].set_title(r'Weekly envelope $W(\tau_w)$')
    axs[1, 0].plot(days, yearly, color='tab:green')
    axs[1, 0].set_title(r'Yearly envelope $Y(\tau_y)$')
    axs[1, 1].axis('off')
    axs[1, 1].text(0.05, 0.75, r'General: $N_c(t) = \sum_g N_g(t) A_g(t) M_g(t)$', fontsize=10)
    axs[1, 1].text(0.05, 0.50, r'Reference: $N_c(t) = A N_{tot}(t) D(\tau_d) W(\tau_w) Y(\tau_y)$', fontsize=10)
    axs[1, 1].text(0.05, 0.25, r'$D$ carries units; $W$ and $Y$ are mean-one envelopes', fontsize=10)
    for ax in axs.flat[:3]:
        ax.grid(alpha=0.25)
    fig.suptitle('Time-scale decomposition')
    fig.tight_layout()
    return save(fig, 'fig_timescale_decomposition', conceptual=True)


def make_revenue_pipeline():
    fig, ax = plt.subplots(figsize=(8.2, 2.6))
    ax.axis('off')
    labels = [
        'Population\nreservoir',
        r'Arrival rate\n$N_c(t)$',
        'Expected spend\nper customer',
        'Revenue\nand costs',
        'Profit',
    ]
    x_positions = np.linspace(0.08, 0.92, len(labels))
    for x, label in zip(x_positions, labels):
        box = plt.Rectangle((x - 0.08, 0.38), 0.16, 0.24, fill=False, linewidth=1.8)
        ax.add_patch(box)
        ax.text(x, 0.50, label, ha='center', va='center', fontsize=10)
    for left, right in zip(x_positions[:-1], x_positions[1:]):
        ax.annotate('', xy=(right - 0.09, 0.50), xytext=(left + 0.09, 0.50), arrowprops=dict(arrowstyle='->', linewidth=1.7))
    ax.set_title('Revenue construction pipeline')
    return save(fig, 'fig_revenue_pipeline', conceptual=True)


def make_daily_patterns(cfg):
    hours = np.linspace(0.0, 24.0, 400)
    weekday = normalized_gaussian_sum(hours, cfg['daily_peaks'], cfg['nu'])
    weekend_peaks = [[amp * 0.9, mu, sigma * 1.1] for amp, mu, sigma in cfg['daily_peaks']]
    weekend = normalized_gaussian_sum(hours, weekend_peaks, cfg['nu'])
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.plot(hours, weekday, label='Weekday', linewidth=2.1)
    ax.plot(hours, weekend, label='Weekend', linewidth=2.1)
    ax.set_xlabel('Hour of day')
    ax.set_ylabel(r'Arrival intensity $[h^{-1}]$')
    ax.set_title('Daily kernels')
    ax.grid(alpha=0.25)
    ax.legend()
    return save(fig, 'fig_daily_patterns', conceptual=False)


def make_weekly_pattern(cfg):
    hours = np.linspace(0.0, 7.0 * 24.0, 7 * 24 * 4 + 1)
    weekly = week_weight_series(hours, cfg['week_weights'])
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.plot(hours / 24.0, weekly, linewidth=2.1)
    ax.set_xlabel('Day of week')
    ax.set_ylabel('Envelope value')
    ax.set_title('Weekly modulation')
    ax.grid(alpha=0.25)
    return save(fig, 'fig_weekly_pattern', conceptual=False)


def make_yearly_pattern(cfg):
    days = np.linspace(0.0, 365.0, 365)
    yearly = yearly_envelope(days, cfg['yearly'])
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.plot(days, yearly, linewidth=2.1)
    ax.set_xlabel('Day of year')
    ax.set_ylabel('Envelope value')
    ax.set_title('Yearly modulation')
    ax.grid(alpha=0.25)
    return save(fig, 'fig_yearly_pattern', conceptual=False)


def make_menu_profiles(items):
    hours = np.linspace(0.0, 24.0, 400)
    profiles = service_profiles(hours)
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for service, profile in profiles.items():
        ax.plot(hours, profile, label=service.capitalize(), linewidth=2.1)
    ax.set_xlabel('Hour of day')
    ax.set_ylabel(r'Normalized service profile $[h^{-1}]$')
    ax.set_title('Menu time profiles by service')
    ax.grid(alpha=0.25)
    ax.legend()
    return save(fig, 'fig_menu_time_profiles', conceptual=False)


def case_timeseries(cfg, include_transit=False, year=False):
    if 'N_total' in cfg:
        total_population = cfg['N_total']
    else:
        _, nliving, nworking, ntransit = richer_population(cfg, include_transit=include_transit)
        total_population = nliving + nworking + ntransit
    A = product(cfg['A_factors'].values())
    total_hours = 365.0 * 24.0 if year else 31.0 * 24.0
    hours = np.linspace(0.0, total_hours, int(total_hours * 4) + 1)
    tod = hours % 24.0
    daily = normalized_gaussian_sum(tod, cfg['daily_peaks'], cfg['nu'])
    weekly = week_weight_series(hours, cfg['week_weights'])
    yearly = yearly_envelope(hours / 24.0, cfg['yearly'])
    nc = total_population * A * daily * weekly * yearly
    spend_per_customer, prod_cost_per_customer, per_item = expected_spend_curves(tod, cfg['items'])
    fee = fee_factor(cfg['fee_methods'])
    revenue_rate = nc * spend_per_customer
    prod_cost_rate = nc * prod_cost_per_customer
    fee_rate = revenue_rate * fee
    hours_per_day = hours[1] - hours[0]
    fixed_rate = (cfg['recurring_daily_cost'] + cfg['staff_daily_cost'] + cfg['fixed_daily_equivalent']) / 24.0
    total_cost_rate = prod_cost_rate + fee_rate + fixed_rate
    profit_rate = revenue_rate - total_cost_rate
    return {
        'hours': hours,
        'tod': tod,
        'nc': nc,
        'revenue_rate': revenue_rate,
        'prod_cost_rate': prod_cost_rate,
        'fee_rate': fee_rate,
        'total_cost_rate': total_cost_rate,
        'profit_rate': profit_rate,
        'per_item': per_item,
    }


def make_service_figures(cfg):
    data = case_timeseries(cfg, include_transit=False, year=False)
    hours = data['hours']
    days = hours / 24.0
    breakfast_mask = [name for name, item in data['per_item'].items() if item['service'] == 'breakfast']
    lunch_mask = [name for name, item in data['per_item'].items() if item['service'] == 'lunch']

    def aggregate(items):
        revenue = np.zeros_like(hours)
        cost = np.zeros_like(hours)
        for name in items:
            revenue += data['nc'] * data['per_item'][name]['revenue_curve']
            cost += data['nc'] * data['per_item'][name]['cost_curve']
        fee = revenue * fee_factor(cfg['fee_methods'])
        profit = revenue - cost - fee
        return revenue, cost + fee, profit

    breakfast_rev, breakfast_cost, breakfast_profit = aggregate(breakfast_mask)
    lunch_rev, lunch_cost, lunch_profit = aggregate(lunch_mask)

    fig1, ax1 = plt.subplots(figsize=(7.2, 3.9))
    ax1.plot(days, breakfast_rev, label='Revenue', linewidth=2.0)
    ax1.plot(days, breakfast_cost, label='Costs', linewidth=2.0)
    ax1.plot(days, breakfast_profit, label='Profit', linewidth=2.0)
    ax1.set_xlabel('Day index')
    ax1.set_ylabel('Currency / hour')
    ax1.set_title('Pedagogical breakfast service')
    ax1.grid(alpha=0.25)
    ax1.legend()
    out1 = save(fig1, 'Fig_breakfast', conceptual=False)

    fig2, ax2 = plt.subplots(figsize=(7.2, 3.9))
    ax2.plot(days, lunch_rev, label='Revenue', linewidth=2.0)
    ax2.plot(days, lunch_cost, label='Costs', linewidth=2.0)
    ax2.plot(days, lunch_profit, label='Profit', linewidth=2.0)
    ax2.set_xlabel('Day index')
    ax2.set_ylabel('Currency / hour')
    ax2.set_title('Pedagogical lunch service')
    ax2.grid(alpha=0.25)
    ax2.legend()
    out2 = save(fig2, 'Fig_main_afternoon', conceptual=False)
    return out1 + out2


def make_summary_figures(cfg):
    jan_data = case_timeseries(cfg, include_transit=False, year=False)
    hours = jan_data['hours']
    days = np.floor(hours / 24.0).astype(int)
    unique_days = np.arange(days.max() + 1)
    daily_revenue = []
    daily_cost = []
    for day in unique_days:
        mask = days == day
        daily_revenue.append(np.trapezoid(jan_data['revenue_rate'][mask], hours[mask]))
        daily_cost.append(np.trapezoid(jan_data['total_cost_rate'][mask], hours[mask]))
    daily_revenue = np.asarray(daily_revenue)
    daily_cost = np.asarray(daily_cost)
    daily_profit = daily_revenue - daily_cost
    fig1, ax1 = plt.subplots(figsize=(7.4, 4.0))
    ax1.plot(unique_days + 1, daily_revenue, label='Revenue', linewidth=2.0)
    ax1.plot(unique_days + 1, daily_cost, label='Costs', linewidth=2.0)
    ax1.plot(unique_days + 1, daily_profit, label='Profit', linewidth=2.0)
    ax1.set_xlabel('Day of month')
    ax1.set_ylabel('Currency / day')
    ax1.set_title('Richer example over one month')
    ax1.grid(alpha=0.25)
    ax1.legend()
    out1 = save(fig1, 'Fig_Jan', conceptual=False)

    year_data = case_timeseries(cfg, include_transit=False, year=True)
    monthly = monthly_totals(year_data['hours'], year_data['revenue_rate'], year_data['total_cost_rate'])
    revenue = np.asarray([item[0] for item in monthly])
    costs = np.asarray([item[1] for item in monthly])
    profit = revenue - costs
    months = np.arange(1, 13)
    width = 0.25
    fig2, ax2 = plt.subplots(figsize=(8.0, 4.2))
    ax2.bar(months - width, revenue, width=width, label='Revenue')
    ax2.bar(months, costs, width=width, label='Costs')
    ax2.bar(months + width, profit, width=width, label='Profit')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Currency / month')
    ax2.set_title('Richer example over one year')
    ax2.grid(alpha=0.2, axis='y')
    ax2.legend()
    out2 = save(fig2, 'Fig_Year', conceptual=False)
    return out1 + out2


def main():
    GRAPHICS.mkdir(parents=True, exist_ok=True)
    params = json.loads(PARAMS_PATH.read_text(encoding='ascii'))
    manifest = {
        'script': str(Path(__file__).relative_to(ROOT)),
        'params': str(PARAMS_PATH.relative_to(ROOT)),
        'outputs': {}
    }
    manifest['outputs']['fig_population_schematic'] = make_population_schematic(params['richer'])
    manifest['outputs']['fig_kernel_comparison'] = make_kernel_comparison(params['richer'])
    manifest['outputs']['fig_timescale_decomposition'] = make_timescale_decomposition(params['pedagogical'])
    manifest['outputs']['fig_revenue_pipeline'] = make_revenue_pipeline()
    manifest['outputs']['fig_daily_patterns'] = make_daily_patterns(params['pedagogical'])
    manifest['outputs']['fig_weekly_pattern'] = make_weekly_pattern(params['pedagogical'])
    manifest['outputs']['fig_yearly_pattern'] = make_yearly_pattern(params['richer'])
    manifest['outputs']['fig_menu_time_profiles'] = make_menu_profiles(params['pedagogical']['items'])
    manifest['outputs']['service_figures'] = make_service_figures(params['pedagogical'])
    manifest['outputs']['summary_figures'] = make_summary_figures(params['richer'])
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding='ascii')
    print('Generated theory figures')


if __name__ == '__main__':
    main()
