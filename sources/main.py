import json
from functions_population import *
from functions_income import *
from error_checks import *
from misc import *

def create_zones(use_fontsize=7):
    '''
        Instructions to divide the plot area into 3 subplot zones
    '''
    fig = plt.figure(layout=None, facecolor='0.9', num=1, clear=True)
    gs = fig.add_gridspec(nrows=11, ncols=8, left=0.1, right=0.90, hspace=0.05, wspace=0.04)
    ax_Nc = fig.add_subplot(gs[0:2, :-2]) # ZONE FOR The number of people
    ax_Nc.tick_params(labelsize=use_fontsize)
    ax_ERI = fig.add_subplot(gs[2:11, :-2]) # ZONE FOR The Expenses, Revenues, Incomes
    ax_ERI.tick_params(labelsize=use_fontsize) 
    ax_text = fig.add_subplot(gs[0:11, -2:]) # ZONE FOR TEXT
    ax_text.spines['top'].set_visible(False)
    ax_text.spines['right'].set_visible(False)
    ax_text.spines['bottom'].set_visible(False)
    ax_text.spines['left'].set_visible(False)
    ax_text.tick_params(left = False, right = False , labelleft = False , labelbottom = False, bottom = False)
    return fig, ax_Nc, ax_ERI, ax_text

def main(dir_data='../data/', test_menu_setup_file='../setup/tests/menu_setup_test.json',
        test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
        test_population_setup_file='../setup/tests/population_setup_test.json',
        test_expenses_setup_file='../setup/tests/expenses_setup_test.json'):
    
    # --- Some definitions ---
    use_fontsize=7
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
    time_day_Nc, Nc_day=integrate(time_hours, Nc_hours, Dt)
    time_day_Nc_weekday, Nc_day_weekday=integrate(time_hours, Nc_weekday_hours, Dt)
    time_day_Nc_weekend, Nc_day_weekend=integrate(time_hours, Nc_weekend_hours, Dt)
    time_day_Nc=time_day_Nc[:-1]
    time_day_Nc_weekday=time_day_Nc_weekday[:-1]
    time_day_Nc_weekend=time_day_Nc_weekend[:-1]
    Nc_day=Nc_day[:-1]
    Dt=7 # Number of days in a week
    time_week_Nc, Nc_week=integrate(time_day_Nc, Nc_day, Dt)
    Dt=month_in_days # Average Number of days in a month
    time_month_Nc, Nc_month=integrate(time_day_Nc, Nc_day, Dt)  
    '''
    # Debug lines 
    fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
    ax2=ax.twinx()
    ax.plot(time_hours, Nc_hours, label='Nc_hours', color='red')
    ax2.plot(time_day_Nc*24, Nc_day/24, label='Nc_day', color='blue')
    t_int_day, Nc_int_day=integrate(time_hours, Nc_hours, 24)
    ax2.plot(t_int_day*24, Nc_int_day, color='green', marker='o')
    ax.legend()
    plt.show()
    exit()
    '''
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
        I = R_menu[i, posOK] - E_menu[i, posOK]
        fig, ax_Nc, ax_ERI, ax_text=create_zones()
        #ax_Nc.bar(time_day[posOK], Nc_day[posOK], label="Nc")
        ax_Nc.bar(time_day[posOK], Nc_day_weekday[posOK], label="Nc_WD", color='blue')
        ax_Nc.bar(time_day[posOK], Nc_day_weekend[posOK], label="Nc_WE", color='red')
        #ax_Nc.legend(fontsize=use_fontsize)
        for j in posOK:
            ax_Nc.text(time_day[j], Nc_day[j]*0.5 , "{:.1f}".format(Nc_day[j]), horizontalalignment='center', fontsize=use_fontsize)
        #fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
        ax_ERI2 = ax_ERI.twinx()
        ax_ERI2.tick_params(axis='y', labelsize=use_fontsize, direction="in") 
        #ax_ERI.set_title(item_names[i])
        ax_text.text(0.5, 0.95, item_names[i], transform=ax_text.transAxes, fontsize=use_fontsize, horizontalalignment='center')
        ax_ERI.bar(time_day[posOK], R_menu[i, posOK], label="Revenues", color='blue') 
        ax_ERI.bar(time_day[posOK], E_menu[i, posOK], label="Expenses", color='red') 
        ax_ERI.legend(fontsize=use_fontsize)
        ax_ERI.grid(axis = 'x')
        ax_ERI.set_xticks(time_day[posOK], day_names)
        ax_ERI.set_ylabel("Revenues & expenses  per items on WEEK 1 (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
        ax_ERI.set_xlabel("Time (days)", fontsize=use_fontsize)
        #
        ax_ERI2.plot(time_day[posOK], I, label="Revenues", color='green', marker="o") 
        ax_ERI2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
        ax_ERI2.yaxis.label.set_color('green')
        ax_ERI2.set_ylim(0, np.max(I)*1.1 )
        ax_ERI2.tick_params(axis='y', colors='green')
        fig.savefig(dir_out_menu_items + 'Fig_' + item_names[i] + '.jpg', dpi=300)
    #
    # Show the daily integrated revenue, expenses and incomes for each month of the year
    #
    k=-1
    for i in range(len(time_month)-1):
        posOK=np.where(np.bitwise_and(time_day >= i*month_in_days, time_day < (i+1)*month_in_days))[0]
        I=R_menu_day[posOK] - E_menu_day[posOK]
        fig, ax_Nc, ax_ERI, ax_text=create_zones()
        #ax_Nc.bar(time_day[posOK], Nc_day[posOK], label="Nc")
        ax_Nc.bar(time_day[posOK], Nc_day_weekday[posOK], label="Nc_WD", color='blue')
        ax_Nc.bar(time_day[posOK], Nc_day_weekend[posOK], label="Nc_WE", color='red')
        #ax_Nc.legend(fontsize=use_fontsize)
        for j in posOK:
            ax_Nc.text(time_day[j], Nc_day[j]*0.3 , "{:.1f}".format(Nc_day[j]), horizontalalignment='center', fontsize=use_fontsize, rotation=90)
        #fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
        ax_ERI2 = ax_ERI.twinx()
        ax_ERI2.tick_params(axis='y', labelsize=use_fontsize, direction="in") 
        ax_ERI.bar(time_day[posOK], R_menu_day[posOK], label="Revenues", color='blue') 
        ax_ERI.bar(time_day[posOK], E_menu_day[posOK], label="Expenses", color='red') 
        ax_ERI.legend(fontsize=use_fontsize)
        #for j in range(0, int(np.floor(month_in_days)), 7):
        #    ax.axvline(x=np.min(time_day[posOK]) + j, color='gray')
        for j in posOK:
            if k>=6:
                k=0
            else:
                k=k+1
            #print(time_day[j], np.max(I)*1.1*0.1, day_names[k])
            ax_ERI2.text(time_day[j], np.max(I)*1.1*0.1 , day_names[k], rotation=90, horizontalalignment='center', fontsize=use_fontsize)
        #ax.grid(axis = 'x')
        ax_ERI2.plot(time_day[posOK], I, label="Revenues", color='green', marker="o") 
        #ax.set_xticks(np.linspace(i*month_in_days, 30*(month_in_days + 1), 31))
        ax_ERI.set_ylabel("Revenues & expenses (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
        ax_ERI.set_xlabel("Time (days since 01 Jan)", fontsize=use_fontsize)
        ax_ERI2.set_ylim(0, np.max(I)*1.1 )
        ax_ERI2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
        ax_ERI2.yaxis.label.set_color('green')
        ax_ERI2.tick_params(axis='y', colors='green')
        fig.savefig(dir_out_monthly_summary + 'Fig_' + month_names[i] + '.jpg', dpi=300)
    #
    # Yearly summary
    fig, ax_Nc, ax_ERI, ax_text=create_zones()
    ax_Nc.bar(time_month, Nc_month, label="Nc")
    #ax_Nc.legend(fontsize=use_fontsize)
    for j in range(len(time_month)):
        ax_Nc.text(time_month[j], Nc_month[j]*0.3 , "{:.1f}".format(Nc_month[j]), horizontalalignment='center', fontsize=use_fontsize, rotation=90)
    #fig, ax = plt.subplots(1, figsize=(12, 6), num=1, clear=True)
    ax_ERI2 = ax_ERI.twinx()
    ax_ERI2.tick_params(axis='y', labelsize=use_fontsize, direction="in") 
    ax_ERI.bar(time_month, R_menu_month, label="Revenues", color='blue') 
    ax_ERI.bar(time_month, E_menu_month, label="Expenses", color='red') 
    ax_ERI.legend(fontsize=8)
    ax_ERI.grid(axis = 'x')
    ax_ERI2.plot(time_month, R_menu_month - E_menu_month, label="Revenues", color='green', marker="o") 
    ax_ERI.set_xticks([0, 1,2,3,4, 5, 6, 7, 8, 9, 10, 11], month_names)
    ax_ERI.set_ylabel("Revenues & expenses (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
    ax_ERI.set_xlabel("Time (months)", fontsize=use_fontsize)
    ax_ERI2.set_ylim(0, np.max(R_menu_month - E_menu_month)*1.1 )
    ax_ERI2.set_ylabel("Incomes  (" + menu_setup["unit"] + ")", fontsize=use_fontsize)
    ax_ERI2.yaxis.label.set_color('green')
    ax_ERI2.tick_params(axis='y', colors='green', labelsize=use_fontsize)
    fig.savefig(dir_out_yearly_summary + 'Fig_Year.jpg', dpi=300)


'''
# Restaurant Test
main(dir_data='../data/', test_menu_setup_file='../setup/tests/menu_setup_test.json',
        test_behavior_setup_file='../setup/tests/behavior_setup_test.json', 
        test_population_setup_file='../setup/tests/population_setup_test.json',
        test_expenses_setup_file='../setup/tests/expenses_setup_test.json')
'''
main(test_menu_setup_file='../setup/tests/menu_setup_R1.json',
        test_behavior_setup_file='../setup/tests/behavior_setup_R1.json', 
        test_population_setup_file='../setup/tests/population_setup_R1.json',
        test_expenses_setup_file='../setup/tests/expenses_setup_R1.json')