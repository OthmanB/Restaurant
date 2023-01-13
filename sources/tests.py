import matplotlib.pyplot as plt
import numpy as np
from functions_population import daily_base_fct
from functions_population import weekly_fct
from functions_population import yearly_fct
from functions_population import compute_Nc
from functions_income import *
from error_checks import *
from scipy.integrate import simpson
import json

#Visualisation of daily_fct() over a specific time interval 
def test_daily_fct():
    hour=np.linspace(0,24, 200)
    params=[[0.3, 7, 0.5], [0.5, 12, 1], [0.2, 18, 1]]
    F=daily_base_fct(hour, params, normalise=False)
    plt.plot(hour, F)
    plt.show()

def test_weekly_fct(test_setup_file='../setup/tests/behavior_setup_test.json'):
    '''
        Visualisation of weekly_fct() using parameters for tests as in the test_setup_file
    '''
    f=open(test_setup_file)
    setup=json.load(f)
    f.close()
    time_h, afluence_h=weekly_fct(setup)
    plt.plot(time_h/24., afluence_h)
    plt.show()

def test_yearly_fct(test_setup_file='../setup/tests/behavior_setup_test.json'):
    '''
        Visualisation of yearly_fct() using parameters for tests as in the test_setup_file
    '''
    f=open(test_setup_file)
    setup=json.load(f)
    f.close()
    time_h, afluence_h=yearly_fct(setup)
    plt.plot(time_h/24., afluence_h)
    plt.show()

def test_compute_Nc(test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
                    test_population_setup_file='../setup/tests/population_setup_test.json'):
    f=open(test_behavior_setup_file)
    behavior_setup=json.load(f)
    f.close()
    f=open(test_population_setup_file)
    population_setup=json.load(f)
    f.close()
    time, Nc_weekday, Nc_weekend=compute_Nc(behavior_setup, population_setup)
    plt.plot(time/24, Nc_weekend)
    plt.plot(time/24, Nc_weekday)
    plt.show()

# --------------------

def test_revenue_menuitem(test_menu_setup_file='../setup/tests/menu_setup_test.json',
                    test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
                    test_population_setup_file='../setup/tests/population_setup_test.json'):
    f=open(test_behavior_setup_file)
    behavior_setup=json.load(f)
    f.close()
    f=open(test_population_setup_file)
    population_setup=json.load(f)
    f.close()
    f=open(test_menu_setup_file)
    menu_setup=json.load(f)
    f.close()

    # Yearly curve of number of clients
    time_hours, Nc_weekday, Nc_weekend=compute_Nc(behavior_setup, population_setup) 
    # Consistency check on the duration and size of the vectors
    err_codes_0=check_time_is_1y(time_hours, y=Nc_weekday)
    if err_codes_0[0] != False:
        print(err_codes_0)
        exit()   
    err_codes_1=check_time_is_1y(time_hours, y=Nc_weekend)
    if err_codes_1[0] != False:
        print(err_codes_1)
        exit()
    Nc=Nc_weekday + Nc_weekend
    # ---  Calculate the expenses related to the menus modulo the requested period ---
    # First, create a daily expenses curve R_menu(t). This is made in hours units
    tmin=np.min(time_hours)
    tmax=24 # tmax is in hours
    Ndishes=len(menu_setup["menu_items"])
    Ndays=int(np.max(time_hours)/24) # Should be 365
    if Ndays != 365:
        print("Error in test_revenue_menuitem(): We should have Ndays = 365 by definition for a year")
        exit()
    R_menu=np.zeros((Ndishes, Ndays))
    R_menu=np.zeros((Ndishes, Ndays))
    time_day=[]
    for day_i in range(Ndays):
        pos_ok=np.where(np.bitwise_and(time_hours >= tmin, time_hours <= tmax))[0]
        item_index=0
        item_name=[]
        for item in menu_setup["menu_items"]:
            R_t_distrib=revenue_menuitem(menu_setup, item, time_hours[pos_ok], Nc[pos_ok], return_sale_distrib=False)
            R_day=simpson(R_t_distrib, time_hours[pos_ok])
            ''' # WARNING: THIS WILL LOOP ALL OVER THE YEAR... A LOT OF PLOTS. Will need to do a simple typical representation for a day later
            fig, ax = plt.subplots()
            ax.plot(time_hours[pos_ok], R_t)
            ax.set_title(item)
            ax.set_ylabel(menu_setup["unit"] + ' per hour')
            ax.set_xlabel("Time (hours)")
            ax.text(0.05, 0.9, "R_day = {:.2f} {}".format(R_day, menu_setup["unit"]), transform=ax.transAxes)
            plt.show()
            fig.clear()
            '''
            R_menu[item_index, day_i]=R_day
            item_index = item_index + 1
            item_name.append(item)
        tmin=tmax
        tmax=tmax + 24
        time_day.append(day_i)
    time_day=np.asarray(time_day, dtype=float)
    #
    # Show all of the curves per item + compute the daily revenue
    #
    R_tot_menu_day=np.zeros(Ndays)
    fig, ax = plt.subplots()
    for i in range(len(menu_setup["menu_items"])):
        print(item_name[i])
        R_tot_menu_day=R_tot_menu_day + R_menu[i,:]
        ax.plot(time_day, R_menu[i, :], label=item_name[i])
        ax.set_ylabel("Daily revenues per items (" + menu_setup["unit"] + ")")
        ax.set_xlabel("Time (days)")
    ax.legend()
    fig.show()
    #
    # Show the daily integrated revenue
    #
    fig, ax = plt.subplots()
    ax.plot(time_day, R_tot_menu_day, label='Total Revenues per day')
    ax.set_ylabel("Total daily revenues (" + menu_setup["unit"] + ")")
    ax.set_xlabel("Time (days)")
    fig.show()
    #
    # Show the monthly integrated revenue
    #
    Dt=30.41666666666 # Average number of days in a month
    time_month=[]
    R_tot_menu_month=[]
    tmin=0
    tmax=Dt
    month_i=1
    while tmin <= np.max(time_day):
        posOK=np.where(np.bitwise_and(time_day >= tmin, time_day <= tmax))[0]
        R_tot_menu_month.append(np.sum(R_tot_menu_day[posOK]))
        time_month.append(month_i)
        tmin=tmax
        tmax=tmax+Dt
        month_i=month_i + 1
    time_month=np.asarray(time_month, dtype=float)
    R_tot_menu_month=np.asarray(R_tot_menu_month, dtype=float)
    fig, ax = plt.subplots()
    ax.plot(time_month, R_tot_menu_month, label='Total Revenues per month')
    ax.set_ylabel("Total monthly revenues (" + menu_setup["unit"] + ")")
    ax.set_xlabel("Time (months)")
    fig.show()


def test_expenses_menuitem(test_menu_setup_file='../setup/tests/menu_setup_test.json',
                    test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
                    test_population_setup_file='../setup/tests/population_setup_test.json'):
    f=open(test_behavior_setup_file)
    behavior_setup=json.load(f)
    f.close()
    f=open(test_population_setup_file)
    population_setup=json.load(f)
    f.close()
    f=open(test_menu_setup_file)
    menu_setup=json.load(f)
    f.close()

    # Yearly curve of number of clients
    time_hours, Nc_weekday, Nc_weekend=compute_Nc(behavior_setup, population_setup) 
    # Consistency check on the duration and size of the vectors
    err_codes_0=check_time_is_1y(time_hours, y=Nc_weekday)
    if err_codes_0[0] != False:
        print(err_codes_0)
        exit()   
    err_codes_1=check_time_is_1y(time_hours, y=Nc_weekend)
    if err_codes_1[0] != False:
        print(err_codes_1)
        exit()
    Nc=Nc_weekday + Nc_weekend
    # ---  Calculate the expenses related to the menus modulo the requested period ---
    # First, create a daily expenses curve E_menu(t). This is made in hours units
    tmin=np.min(time_hours)
    tmax=24 # tmax is in hours
    Ndishes=len(menu_setup["menu_items"])
    Ndays=int(np.max(time_hours)/24) # Should be 365
    if Ndays != 365:
        print("Error in test_revenue_menuitem(): We should have Ndays = 365 by definition for a year")
        exit()
    E_menu=np.zeros((Ndishes, Ndays))
    E_menu=np.zeros((Ndishes, Ndays))
    time_day=[]
    for day_i in range(Ndays):
        pos_ok=np.where(np.bitwise_and(time_hours >= tmin, time_hours <= tmax))[0]
        item_index=0
        item_name=[]
        for item in menu_setup["menu_items"]:
            E_t_distrib=expenses_menuitem(menu_setup, item, time_hours[pos_ok], Nc[pos_ok], return_sale_distrib=False)
            E_day=simpson(E_t_distrib, time_hours[pos_ok])
            ''' # WARNING: THIS WILL LOOP ALL OVER THE YEAR... A LOT OF PLOTS. Will need to do a simple typical representation for a day later
            fig, ax = plt.subplots()
            ax.plot(time_hours[pos_ok], E_t)
            ax.set_title(item)
            ax.set_ylabel(menu_setup["unit"] + ' per hour')
            ax.set_xlabel("Time (hours)")
            ax.text(0.05, 0.9, "E_day = {:.2f} {}".format(E_day, menu_setup["unit"]), transform=ax.transAxes)
            plt.show()
            fig.clear()
            '''
            E_menu[item_index, day_i]=E_day
            item_index = item_index + 1
            item_name.append(item)
        tmin=tmax
        tmax=tmax + 24
        time_day.append(day_i)
    time_day=np.asarray(time_day, dtype=float)
    #
    # Show all of the curves per item + compute the daily revenue
    #
    E_tot_menu_day=np.zeros(Ndays)
    fig, ax = plt.subplots()
    for i in range(len(menu_setup["menu_items"])):
        print(item_name[i])
        E_tot_menu_day=E_tot_menu_day + E_menu[i,:]
        ax.plot(time_day, E_menu[i, :], label=item_name[i])
        ax.set_ylabel("Daily revenues per items (" + menu_setup["unit"] + ")")
        ax.set_xlabel("Time (days)")
    ax.legend()
    fig.show()
    #
    # Show the daily integrated revenue
    #
    fig, ax = plt.subplots()
    ax.plot(time_day, E_tot_menu_day, label='Total Revenues per day')
    ax.set_ylabel("Total daily revenues (" + menu_setup["unit"] + ")")
    ax.set_xlabel("Time (days)")
    fig.show()
    #
    # Show the monthly integrated revenue
    #
    Dt=30.41666666666 # Average number of days in a month
    time_month=[]
    E_tot_menu_month=[]
    tmin=0
    tmax=Dt
    month_i=1
    while tmin <= np.max(time_day):
        posOK=np.where(np.bitwise_and(time_day >= tmin, time_day <= tmax))[0]
        E_tot_menu_month.append(np.sum(E_tot_menu_day[posOK]))
        time_month.append(month_i)
        tmin=tmax
        tmax=tmax+Dt
        month_i=month_i + 1
    time_month=np.asarray(time_month, dtype=float)
    E_tot_menu_month=np.asarray(E_tot_menu_month, dtype=float)
    fig, ax = plt.subplots()
    ax.plot(time_month, E_tot_menu_month, label='Total Revenues per month')
    ax.set_ylabel("Total monthly revenues (" + menu_setup["unit"] + ")")
    ax.set_xlabel("Time (months)")
    fig.show()

