from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from simulation_api import simulate_year
from config_loader import (
    load_menu_config,
    load_behavior_config,
    load_population_config,
    load_expenses_config,
)


def create_zones(use_fontsize=7):
    # Instructions to divide the plot area into 3 subplot zones
    fig = plt.figure(layout=None, facecolor='0.9', num=1, clear=True)
    gs = fig.add_gridspec(nrows=11, ncols=8, left=0.1, right=0.90, hspace=0.05, wspace=0.04)
    ax_Nc = fig.add_subplot(gs[0:2, :-2])
    ax_Nc.tick_params(labelsize=use_fontsize)
    ax_ERI = fig.add_subplot(gs[2:11, :-2])
    ax_ERI.tick_params(labelsize=use_fontsize)
    ax_text = fig.add_subplot(gs[0:11, -2:])
    ax_text.spines['top'].set_visible(False)
    ax_text.spines['right'].set_visible(False)
    ax_text.spines['bottom'].set_visible(False)
    ax_text.spines['left'].set_visible(False)
    ax_text.tick_params(left=False, right=False, labelleft=False, labelbottom=False, bottom=False)
    return fig, ax_Nc, ax_ERI, ax_text


def _ensure_output_dirs(dir_data):
    dir_out_menu_items = dir_data + '/plots/menu_items/'
    dir_out_monthly_summary = dir_data + '/plots/monthly_summary/'
    dir_out_yearly_summary = dir_data + '/plots/'
    Path(dir_out_menu_items).mkdir(parents=True, exist_ok=True)
    Path(dir_out_monthly_summary).mkdir(parents=True, exist_ok=True)
    Path(dir_out_yearly_summary).mkdir(parents=True, exist_ok=True)
    return dir_out_menu_items, dir_out_monthly_summary, dir_out_yearly_summary


def _load_configs(menu_file, behavior_file, population_file, expenses_file):
    menu_setup = load_menu_config(menu_file)
    behavior_setup = load_behavior_config(behavior_file)
    population_setup = load_population_config(population_file)
    expenses_setup = load_expenses_config(expenses_file)
    return menu_setup, behavior_setup, population_setup, expenses_setup


def main(
    dir_data='data/',
    test_menu_setup_file='setup/menu_setup_R1.yaml',
    test_behavior_setup_file='setup/behavior_setup_r1.yaml',
    test_population_setup_file='setup/population_setup_R1.yaml',
    test_expenses_setup_file='setup/expenses_setup_R1.yaml',
    mode='deterministic',
    seed=None,
):
    use_fontsize = 7

    _, dir_out_monthly_summary, dir_out_yearly_summary = _ensure_output_dirs(dir_data)

    menu_setup, behavior_setup, population_setup, expenses_setup = _load_configs(
        test_menu_setup_file,
        test_behavior_setup_file,
        test_population_setup_file,
        test_expenses_setup_file,
    )

    simulation = simulate_year(
        menu_setup,
        behavior_setup,
        population_setup,
        expenses_setup,
        mode=mode,
        seed=seed,
    )

    month_in_days = simulation['metadata']['month_in_days']
    day_names = simulation['metadata']['day_names']
    month_names = simulation['metadata']['month_names']

    time_day = simulation['time']['day']
    time_month = simulation['time']['month_integrated']
    Nc_day = simulation['population']['Nc_day']
    Nc_day_weekday = simulation['population']['Nc_day_weekday']
    Nc_day_weekend = simulation['population']['Nc_day_weekend']

    R_menu_day = simulation['revenue']['day']
    E_menu_day = simulation['expenses']['menu_day']
    E_tot_day = simulation['expenses']['total_day']

    Nc_month = simulation['population']['Nc_month']
    R_menu_month = simulation['revenue']['month']
    E_menu_month = simulation['expenses']['menu_month']
    E_tot_month = simulation['expenses']['total_month']

    I_month = simulation['income']['month']

    k = -1
    for i in range(len(time_month) - 1):
        posOK = np.where(np.bitwise_and(time_day >= i * month_in_days, time_day < (i + 1) * month_in_days))[0]
        I = R_menu_day[posOK] - E_tot_day[posOK]

        fig, ax_Nc, ax_ERI, _ = create_zones(use_fontsize=use_fontsize)
        ax_Nc.bar(time_day[posOK], Nc_day_weekday[posOK], label='Nc_WD', color='blue')
        ax_Nc.bar(time_day[posOK], Nc_day_weekend[posOK], label='Nc_WE', color='red')
        ax_Nc.set_ylabel('Nclients')

        for j in posOK:
            ax_Nc.text(
                time_day[j],
                Nc_day[j] * 0.3,
                '{:.1f}'.format(Nc_day[j]),
                horizontalalignment='center',
                fontsize=use_fontsize,
                rotation=90,
            )

        ax_ERI2 = ax_ERI.twinx()
        ax_ERI2.tick_params(axis='y', labelsize=use_fontsize, direction='in')
        ax_ERI.bar(time_day[posOK], R_menu_day[posOK], label='Revenues', color='blue')
        ax_ERI.bar(time_day[posOK], E_tot_day[posOK], label='$E_{tot}$', color='orange')
        ax_ERI.bar(time_day[posOK], E_menu_day[posOK], label='$E_{menu}$', color='red')
        ax_ERI.legend(fontsize=use_fontsize)

        for j in posOK:
            if k >= 6:
                k = 0
            else:
                k = k + 1
            ax_ERI2.text(
                time_day[j],
                np.max(I) * 1.1 * 0.1,
                day_names[k],
                rotation=90,
                horizontalalignment='center',
                fontsize=use_fontsize,
            )

        ax_ERI2.plot(time_day[posOK], I, label='Revenues', color='green', marker='o')
        ax_ERI.set_ylabel('Revenues & expenses (' + menu_setup['unit'] + ')', fontsize=use_fontsize)
        ax_ERI.set_xlabel('Time (days since 01 Jan)', fontsize=use_fontsize)
        ax_ERI2.set_ylim(0, np.max(I) * 1.1)
        ax_ERI2.set_ylabel('Incomes  (' + menu_setup['unit'] + ')', fontsize=use_fontsize)
        ax_ERI2.yaxis.label.set_color('green')
        ax_ERI2.tick_params(axis='y', colors='green')
        fig.savefig(dir_out_monthly_summary + 'Fig_' + month_names[i] + '.jpg', dpi=300)

    fig, ax_Nc, ax_ERI, _ = create_zones(use_fontsize=use_fontsize)
    ax_Nc.bar(time_month, Nc_month, label='Nc')
    ax_Nc.set_ylabel('Nclients')

    for j in range(len(time_month)):
        ax_Nc.text(
            time_month[j],
            Nc_month[j] * 0.3,
            '{:.1f}'.format(Nc_month[j]),
            horizontalalignment='center',
            fontsize=use_fontsize,
            rotation=90,
        )
        ax_ERI.text(
            time_month[j],
            R_menu_month[j],
            '{:.1f}'.format(R_menu_month[j]),
            horizontalalignment='center',
            fontsize=use_fontsize,
            rotation=90,
        )

    ax_ERI2 = ax_ERI.twinx()
    ax_ERI2.tick_params(axis='y', labelsize=use_fontsize, direction='in')
    ax_ERI.bar(time_month, R_menu_month, label='Revenues', color='blue')
    ax_ERI.bar(time_month, E_tot_month, label='$E_{tot}$', color='orange')
    ax_ERI.bar(time_month, E_menu_month, label='$E_{Menu}$', color='red')
    ax_ERI.legend(fontsize=use_fontsize)
    ax_ERI.grid(axis='x')
    ax_ERI.set_ylim(0, np.max([np.max(R_menu_month), np.max(E_tot_month)]) * 1.2)

    ax_ERI2.plot(time_month, I_month, label='Revenues', color='green', marker='o')
    ax_ERI.set_xticks([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], month_names)
    ax_ERI.set_ylabel('Revenues & expenses (' + menu_setup['unit'] + ')', fontsize=use_fontsize)
    ax_ERI.set_xlabel('Time (months)', fontsize=use_fontsize)
    ax_ERI2.set_ylim(0, np.max(I_month) * 1.1)
    ax_ERI2.set_ylabel('Incomes  (' + menu_setup['unit'] + ')', fontsize=use_fontsize)
    ax_ERI2.yaxis.label.set_color('green')
    ax_ERI2.tick_params(axis='y', colors='green', labelsize=use_fontsize)
    fig.savefig(dir_out_yearly_summary + 'Fig_Year.jpg', dpi=300)


if __name__ == '__main__':
    main(
        test_menu_setup_file='setup/menu_setup_R1.yaml',
        test_behavior_setup_file='setup/behavior_setup_r1.yaml',
        test_population_setup_file='setup/population_setup_R1.yaml',
        test_expenses_setup_file='setup/expenses_setup_R1.yaml',
        mode='deterministic',
        seed=42,
    )
