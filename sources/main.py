import json
from functions_population import *
from functions_income import *
from error_checks import *
from misc import *


def main(dir_data='../data/', test_menu_setup_file='../setup/tests/menu_setup_test.json',
        test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
        test_population_setup_file='../setup/tests/population_setup_test.json',
        test_expenses_setup_file='../setup/tests/expenses_setup_test.json'):
    
    # --- Some definitions ---
    month_in_days=30.41666666666
    day_indexes=[0, 1,2,3,4, 5, 6]
    day_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_indexes=[0, 1,2,3,4, 5, 6, 7, 8, 9, 10, 11]
    month_names=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # ------------------------
    # --- Define output directories for each kind of outputs ---
    dir_out_menu_items=dir_data + '/plots/menu_items/'
    dir_out_monthly_summary=dir_data + '/plots/monthly_summary/'
    dir_out_yearly_summary=dir_data + '/plots/'
    # ----------------------------------------------------------
    # --- Loading configuration files ---
    f=open(test_menu_setup_file)
    menu_setup=json.load(f)
    f.close()
    f=open(test_behavior_setup_file)
    behavior_setup=json.load(f)
    f.close()
    f=open(test_population_setup_file)
    population_setup=json.load(f)
    f.close()
    f=open(test_expenses_setup_file)
    expenses_setup=json.load(f)
    f.close()
    # -----------------------------------
    #
    # --- Compute the population that comes to the restaurant ----
    # Yearly curve of number of client each hour
    time_hours, Nc_weekday_hours, Nc_weekend_hours=compute_Nc(behavior_setup, population_setup) 
    # Consistency check on the duration and size of the vectors
    err_codes_0=check_time_is_1y(time_hours, y=Nc_weekday_hours)
    if err_codes_0[0] != False:
        print(err_codes_0)
        exit()   
    err_codes_1=check_time_is_1y(time_hours, y=Nc_weekend_hours)
    if err_codes_1[0] != False:
        print(err_codes_1)
        exit()
    Nc_hours=Nc_weekday_hours + Nc_weekend_hours
    # Yearly curve of clients each day
    Dt=24 # Number of hours in a day
    time_day_Nc, Nc_day=sums(time_hours, Nc_hours, Dt)
    time_day_Nc_weekday, Nc_day_weekday=sums(time_hours, Nc_weekday_hours, Dt)
    time_day_Nc_weekend, Nc_day_weekend=sums(time_hours, Nc_weekend_hours, Dt)
    time_day_Nc=time_day_Nc[:-1]
    time_day_Nc_weekday=time_day_Nc_weekday[:-1]
    time_day_Nc_weekend=time_day_Nc_weekend[:-1]
    Nc_day=Nc_day[:-1]
    Dt=7 # Number of days in a week
    time_week_Nc, Nc_week=sums(time_day_Nc, Nc_day, Dt)
    Dt=month_in_days # Average Number of days in a month
    time_month_Nc, Nc_month=sums(time_day_Nc, Nc_day, Dt)  
    # ------------------------------------------------------------
    #
    # --- Compute the Revenues and expenses ---
    # Daily Revenue/Expenses related to each sold goods
    time_day, R_menu, E_menu, item_names=revenues_expenses_menuitem_matrix(menu_setup, time_hours, Nc_hours)
    Ndays = len(time_day)
    # Total Revenues/Expenses for a day related to all sold goods
    R_menu_day=np.zeros(Ndays)
    E_menu_day=np.zeros(Ndays)
    for i in range(len(menu_setup["menu_items"])):
        R_menu_day=R_menu_day + R_menu[i,:]
        E_menu_day=E_menu_day + E_menu[i,:]
    # The Weekly integrated revenues and expenses
    Dt=7 # Number of days in a week
    time_week, R_menu_week=sums(time_day, R_menu_day, Dt)
    time_week, E_menu_week=sums(time_day, E_menu_day, Dt)
    # The Monthly integrated revenues and expenses
    Dt=month_in_days # Average number of days in a month
    time_month, R_menu_month=sums(time_day, R_menu_day, Dt)
    time_month, E_menu_month=sums(time_day, E_menu_day, Dt)
    # Expenses related to the fees. Note that this is a stochastic variable
    E_fees_day=expenses_fees(expenses_setup, R_menu_day, Nc_day)
    E_fees_week=expenses_fees(expenses_setup, R_menu_week, Nc_week)
    E_fees_month=expenses_fees(expenses_setup, R_menu_month, Nc_month)
    # Expenses related to the staff normalised over period of a day, week and month
    E_staff_day=0
    E_staff_week=0
    E_staff_month=0
    for staff in expenses_setup["staff"]["staff_list"]:
        E_staff_day=E_staff_day + expenses_staff(expenses_setup, staff, period=1)
        E_staff_week=E_staff_week + expenses_staff(expenses_setup, staff, period=7)
        E_staff_month=E_staff_month + expenses_staff(expenses_setup, staff)
    # Recurent expenses normalised over periods of a day, week and month
    E_rec_day=expenses_recurent(expenses_setup, period=1)
    E_rec_week=expenses_recurent(expenses_setup, period=7)
    E_rec_month=expenses_recurent(expenses_setup)
    # Total Expenses
    E_tot_day = E_menu_day + E_staff_day + E_rec_day + E_fees_day
    E_tot_week = E_menu_week + E_staff_week + E_rec_week + E_fees_week
    E_tot_month= E_menu_month + E_staff_month + E_rec_month + E_fees_month
    # -----------------------------------------
    #
    # --- Make all the plots ---
    #
    # Show all of the curves per item over the first week only
    #
    posOK=np.where(time_day < 7)[0]
    for i in range(len(menu_setup["menu_items"])):
        fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
        ax2 = ax.twinx()
        ax.set_title(item_names[i])
        ax.plot(time_day[posOK], E_menu[i, posOK], label="Expenses", color='red', marker="o") 
        ax.plot(time_day[posOK], R_menu[i, posOK], label="Revenues", color='blue', marker="o") 
        ax.legend()
        ax.grid(axis = 'x')
        ax2.plot(time_day[posOK], R_menu[i, posOK] - E_menu[i, posOK], label="Revenues", color='green', marker="o") 
        ax.set_xticks(day_indexes, day_names)
        ax.set_ylabel("Revenues & expenses  per items on WEEK 1 (" + menu_setup["unit"] + ")")
        ax.set_xlabel("Time (days)")
        ax2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")")
        ax2.yaxis.label.set_color('green')
        ax2.tick_params(axis='y', colors='green')
        fig.savefig(dir_out_menu_items + 'Fig_' + item_names[i] + '.jpg', dpi=300)
    #
    # Show the daily integrated revenue, expenses and incomes for each month of the year
    #
    cpt=0
    label=[]
    label_indexes=[]
    for i in range(4):
        for d in day_names:
            label.append(d)
            label_indexes.append(cpt)
            cpt=cpt+1
    for i in range(len(time_month)-1):
        posOK=np.where(np.bitwise_and(time_day >= i*month_in_days, time_day < (i+1)*month_in_days))[0]
        fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
        ax2 = ax.twinx()
        ax.plot(time_day[posOK], E_menu_day[posOK], label="Expenses", color='red', marker="o") 
        ax.plot(time_day[posOK], R_menu_day[posOK], label="Revenues", color='blue', marker="o") 
        ax.legend()
        ax.grid(axis = 'x')
        ax2.plot(time_day[posOK], R_menu[i, posOK] - E_menu[i, posOK], label="Revenues", color='green', marker="o") 
        ax.set_xticks(np.linspace(0, 30, 31))
        ax.set_ylabel("Revenues & expenses (" + menu_setup["unit"] + ")")
        ax.set_xlabel("Time (days))")
        ax2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")")
        ax2.yaxis.label.set_color('green')
        ax2.tick_params(axis='y', colors='green')
        fig.savefig(dir_out_monthly_summary + 'Fig_' + month_names[i] + '.jpg', dpi=300)
    #
    fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
    ax2 = ax.twinx()
    ax.plot(time_month, E_menu_month, label="Expenses", color='red', marker="o") 
    ax.plot(time_month, R_menu_month, label="Revenues", color='blue', marker="o") 
    ax.legend()
    ax.grid(axis = 'x')
    ax2.plot(time_month, R_menu_month - E_menu_month, label="Revenues", color='green', marker="o") 
    ax.set_xticks([0, 1,2,3,4, 5, 6, 7, 8, 9, 10, 11], month_names)
    ax.set_ylabel("Revenues & expenses (" + menu_setup["unit"] + ")")
    ax.set_xlabel("Time (months)")
    ax2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")")
    ax2.yaxis.label.set_color('green')
    ax2.tick_params(axis='y', colors='green')
    fig.savefig(dir_out_yearly_summary + 'Fig_Year.jpg', dpi=300)
