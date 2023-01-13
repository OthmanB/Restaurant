'''
Functions used ot compute menu-related content
'''
import json
import numpy as np
from scipy.integrate import simpson
from error_checks import check_time_is_24h
from error_checks import check_time_is_greater_than_period

def time_distrib(x, name, params):
    '''
        Function that selects a requested distribution among a list and returns it
        THIS DOES NOT GENERATE RANDOM NUMBER.
        x: x-axis on which the distribution is created
        name: Name of the function that is going to be returned
        params: The parameters of the function of name 'name'
    '''
    match name:
        case "Gaussian":
            Norm=np.sqrt(2* np.pi) * params[1]
            return np.exp(-(x-params[0])**2/(2*params[1]**2)) / Norm
        case "Uniform":
            # convert x into an array if necessary in order to be able to use the bitwise_and and where function.
            try:
                l=len(x)
            except:
                x=[x]
            r=np.zeros(len(x))
            pos_ok=np.where(np.bitwise_and(x >= params[0], x<=params[1]))
            Norm=1/(params[1] - params[0])
            r[pos_ok]=Norm
            return r
        case _:
            print("Error: Unrecognized case for :", name ," inside time_distrib(). Debug Required.")
            print("       The program will exit now")
            exit()

def revenue_menuitem(menu_setup, item, time_hours, Nc, return_sale_distrib=False):
    '''
        Given a setup json structure for the menu, this function returns the 
        time dependent function for the revenue generated of a given menu item
        menu_setup: The setup json structure for the menu.
        Warning: Mathematically this function only defined over time=[0h,24h]. It is up to the user to be careful
                 that this is respected.
        item: The item we are looking for
        Nc: Population (time-dependent function of the number of clients) coming to the restaurant
        time_hours: Time-vector associated to Nc. Must be of same size as Nc
        Returns: 
            - The population revenue R*Nc
            - The item sales time-distribution
    '''
    # Verify that the user respect mathematical specifications regarding time
    err_codes=check_time_is_24h(time_hours, y=Nc)
    if err_codes[0] != False:
        print('Error code: ', err_codes)
        exit()
    #
    R=menu_setup["menu_items"][item]["price"]*time_distrib(time_hours-np.min(time_hours), menu_setup["menu_items"][item]["time_distribution"]["name"], menu_setup["menu_items"][item]["time_distribution"]["params"] )
    if return_sale_distrib == True:
        return R*Nc, R
    else:
        return R*Nc


def expenses_menuitem(menu_setup, item, time_hours, Nc, return_sale_distrib=False):
    '''
        Given a setup json structure for the menu, this function returns the 
        time dependent function over [0h,24h] for the expenses generated of a given menu item
        Warning: Mathematically this function only defined over tmax - tmin=24h. The user must  be careful
                 that this is respected.
        menu_setup: The setup json structure for the menu
        item: The item we are looking for
        Nc: Population (time-dependent function of the number of clients) coming to the restaurant
        time: Time-vector associated to Nc. Must be of same size as Nc
        Returns: 
            - The population revenue R*Nc
            - The item sales time-distribution    
    '''
    # Verify that the user respect mathematical specifications
    check_time_is_24h(time_hours, y=Nc)
    #
    E=menu_setup["menu_items"][item]["cost"]*time_distrib(time_hours-np.min(time_hours), menu_setup["menu_items"][item]["time_distribution"]["name"], menu_setup["menu_items"][item]["time_distribution"]["params"] )
    if return_sale_distrib == True:
        return E*Nc, E
    else:
        return E*Nc

def expenses_fees(expenses_setup, Rpop, Nc):
    '''
        Fees related to the method of payement
        We use a probabilistic description so that this is a random variable with probability 
        given by the field payement_proba within the menu_expenses json structure.
        expenses_setup: Json structure with all the details of the expenses modeling
        Rpop: The revenues of the shop. expenses due to fees are proportional to the Revenue function (modulo a random variable controling the type of fees)
        Nc: Population (time-dependent function of the number of clients) coming to the restaurant
    '''
    # Check that we have the correct normalisation for the probability and flatten the json content for arithmetic operations
    probas=[] # Probability that client pick a given payment method
    fees=[] # Fees associated to each payment method
    for m in expenses_setup["payment_fees"]["method"]:
        probas.append(expenses_setup["payment_fees"]["method"][m]["payement_proba"])
        fees.append(expenses_setup["payment_fees"]["method"][m]["fees"])
    if np.sum(probas) != 1:
        print("Error: Improper normalisation of the variable 'payment_fees' within the expenses_setup variable.")
        print("       Be sure that all probability sums to 1.")
        print("       Debug required. The program will exit now.")
        exit(-1)
    #
    Nchoices=len(probas) # number of ways of paying (cash and credit card, etc...)
    r=np.random.choice(Nchoices, p=probas) # pick random value
    E=np.zeros(len(Nc))
    for i in range(len(Nc)):
        # Calculates the overall fee incured at a given time using the probabilistic model
        # The greater the number of client, the more the noise is reduced by averaging: We tend towards the asymptotic probability
        Npicks=int(np.round(Nc[i]))
        for k in range(Npicks):
            Ef=Rpop[i]*fees[r]/Npicks 
        E[i]=Ef
    return E

def expenses_staff(expenses_setup, staff_name, period=7):
    '''
        Compute the expenses related to a given staff member on a weekly basis, with the possibility to renormalize it
        over an arbitrary period of time.
        expenses_setup: Json structure with all the details of the expenses modeling
        period: Defines the period (in days) on which the calculation is made. By default, it is a weekly calculation (7 days)
        staff_name: The name of the staff for wich we seek the expenses
    '''
    E_staff_day=0 # Cost of a given staff for all the week days
    for day in expenses_setup["staff"]["staff_list"][staff_name]["working_hours"]:
        for work_intervals in expenses_setup["staff"]["staff_list"][staff_name]["working_hours"][day]: # We access to the list of working intervals
            Delta_hours=work_intervals[1] - work_intervals[0] # Total working hours for a single interval (the staff may work 2h on morning, go home and come back 2h in the evening)
            E_staff_day=E_staff_day + Delta_hours*expenses_setup["staff"]["staff_list"][staff_name]["hourly_rate"] # Sum the working hours for all daily working interval
    # Adjust the calculation period, if necessary
    if period !=7:
        E_staff_day*period/7
    return E_staff_day

def expenses_recurent(expenses_setup, period=30.41666666666):
    '''
        Compute the total of the recurrent expenses assuming that these are monthly expenses (monthly normalisation = 30.4166 days in average per month)
        with the possibility of renormalize it over an arbitrary period of time
        expenses_setup: Json structure with all the details of the expenses modeling
        period: Defines the period (in days) on which the calculation is made. By default, it is a monthly calculation (1 month = 30.4166 days)
    '''
    E_rec=0
    for r in expenses_setup["recurring"]["recurring_list"]:
        E_rec=E_rec + expenses_setup["recurring"]["recurring_list"][r]
    #
    if period !=30.41666666666:
        if period == 30 or period == 31:
            print("Warning: You asked {} days of period normalisation. However, this is close to the average monthly period set by default (30.41666666666)".format(period))
            print("         If you want the duration per month, please do not provide any value for the optional period argument")
            print("         Pursuing...")
        E_rec=E_rec*period/30.41666666666
    return E_rec

def revenues_expenses_menuitem_matrix(menu_setup, time_hours, Nc):
    '''
        Function that calculates the revenues and expenses related to
        all the sold products
        menu_setup: The Json structure containing all the configuration for the menu
        time_hours: The time vector on which the whole daily configuration is calculated
        Nc : The client population vector. Must be of same size as time_hours
    '''
    # ---  Calculate the expenses related to the menus modulo the requested period ---
    # First, create a daily expenses curve E_menu(t). This is made in hours units
    tmin=np.min(time_hours)
    tmax=24 # tmax is in hours
    Ndishes=len(menu_setup["menu_items"])
    Ndays=int(np.max(time_hours)/24) # Should be 365
    if Ndays != 365:
        print("Error in test_revenue_menuitem(): We should have Ndays = 365 by definition for a year")
        exit()
    R_menu=np.zeros((Ndishes, Ndays))
    R_menu=np.zeros((Ndishes, Ndays))
    E_menu=np.zeros((Ndishes, Ndays))
    E_menu=np.zeros((Ndishes, Ndays))
    time_day=[]
    for day_i in range(Ndays):
        pos_ok=np.where(np.bitwise_and(time_hours >= tmin, time_hours <= tmax))[0]
        item_index=0
        item_name=[]
        for item in menu_setup["menu_items"]:
            # -- The daily revenues -- 
            R_t_distrib=revenue_menuitem(menu_setup, item, time_hours[pos_ok], Nc[pos_ok], return_sale_distrib=False)
            R_day=simpson(R_t_distrib, time_hours[pos_ok])
            R_menu[item_index, day_i]=R_day
            # -- The daily expenses --
            E_t_distrib=expenses_menuitem(menu_setup, item, time_hours[pos_ok], Nc[pos_ok], return_sale_distrib=False)
            E_day=simpson(E_t_distrib, time_hours[pos_ok])
            E_menu[item_index, day_i]=E_day
            #
            item_index = item_index + 1
            item_name.append(item)
        tmin=tmax
        tmax=tmax + 24
        time_day.append(day_i)
    time_day=np.asarray(time_day, dtype=float)
    return time_day, R_menu, E_menu, item_name