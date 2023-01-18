'''
Functions used ot compute menu-related content
'''
import json
import numpy as np
from scipy.integrate import simpson
from error_checks import check_period_is_modulo_1
from error_checks import check_is_less_than
#from error_checks import check_time_is_24h
#from error_checks import check_time_is_greater_than_period
from misc import combinations,rem_duplicates, deep_rem_duplicates, list_indexes

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
            Norm=1./(params[1] - params[0])
            r[pos_ok]=Norm
            return r
        case _:
            print("Error: Unrecognized case for :", name ," inside time_distrib(). Debug Required.")
            print("       The program will exit now")
            exit()

def unique_combination_items(menu_setup, debug=False, limit=7):
    '''
        Generate all of the combination provided a list of items
        within the menu_setup Json structure
        limit_by_service: If True, compute the combinations for each service.
            This avoids the explosion of possibilities and allows you to stay below the limit
            The counterpart is that it will not compute combination between different services
        menu_setup: Json structure with the menu configuration
        debug: If True, show text informations about critical steps 
    '''
    #debug=True
    # -- Unpack and format the required menu_setup parameters ---
    names=[]
    proba=[]
    price=[]
    cost=[]
    services=[]
    for m in menu_setup["menu_items"]:
        names.append(m) # item names
        proba.append(menu_setup["menu_items"][m]["daily_proba"])
        price.append(menu_setup["menu_items"][m]["price"])
        cost.append(menu_setup["menu_items"][m]["cost"])
        services.append(menu_setup["menu_items"][m]["service"])
    available_services=rem_duplicates(services, algo='for2') # We use the for2 algo here because otherwise python splits the string into char
    if debug == True:
        print("{0:20s}  {1:30s}  {2:20s}  {3:20s}  {4:20s}".format("service","name", "price", "cost", "proba"))
        for i in range(len(names)):
            print("{0:20s}  {1:30s}  {2:15.2f}  {3:15.2f}  {4:15.2f}".format(services[i], names[i], price[i], cost[i], proba[i]))
    if menu_setup["limit_by_service"] == False:
        err=check_is_less_than(len(names), limit, strict=False)
        if err == True:
            print(" The number of combination will be too large to handle by python list")
            print(" A more efficient computation language is required for lists of items greater than ", limit)
            print(" Try to set limit_by_service = true in the Json configuration file")
            print(" The program will exit the program")
            exit()
        l=[]
        for i in range(len(names)):
            l.append([names[i], proba[i], price[i], cost[i], services[i]])
        combi_all=combinations(l, without_recurence=True)
        combi_unique=deep_rem_duplicates(combi_all)
    else:
        # Here we consider combination per block of service
        combi_unique=[]
        for s in available_services:
            ind=list_indexes(services, s)
            if debug == True:
                print(s)
                print("   ind=", ind)
            err=check_is_less_than(len(ind), limit, strict=False)
            tmp=[]
            for i in ind:
                tmp.append([names[i], proba[i], price[i], cost[i], s])
            if debug == True:
                print(tmp)
            combi_all_tmp=combinations(tmp, without_recurence=True)
            combi_unique_tmp=deep_rem_duplicates(combi_all_tmp)
            for c in combi_unique_tmp:
                combi_unique.append(c)
    #
    if debug == True:
        print('-- Unique Combination --')
        for c in combi_unique:
            print(c)
    #exit()
    return combi_unique, available_services

def daily_revenue_and_cost_menu_items_perclient(menu_setup, debug=False):
    '''
        Using all of the combination of the conditional probabilities for what
        a given client can order (eg. Bread alone, Bacon alone, or Bread + Bacon)
        the function calculates the list of all combinations for a  daily revenue and costs of the sales
        for each costumer
        menu_setup: Json structure with the menu configuration
        debug: If True, show text informations about critical steps
    '''
    # Compute all of the combination
    combi_unique, avail_services=unique_combination_items(menu_setup, debug)
    # Compute the revenue and costs for each combinations
    revenues_combi=[]
    expenses_combi=[]
    services_combi=[]
    for c in combi_unique:
        proba_joint=1
        price_paid=0
        price_cost=0
        s_tmp=[]
        for cc in c:
            proba_joint=proba_joint*cc[1]
            price_paid=price_paid + cc[2]
            price_cost=price_cost + cc[3]
            if menu_setup["limit_by_service"] == False:
                s_tmp.append(cc[4])
        revenues_combi.append(proba_joint*price_paid)
        expenses_combi.append(proba_joint*price_cost)
        if menu_setup["limit_by_service"] == False: # We keep all of the service entries
            services_combi.append(s_tmp)
        else: # All field of services will be the same, by definition, so we just keep one value
            services_combi.append(c[0][4])
    if debug == True:
        for i in range(len(combi_unique)):
            print("[", i, "] Combi: ", combi_unique[i])
            print( "   revenues_combi = ", revenues_combi[i] )
            print( "   expenses_combi = ", expenses_combi[i] )
    return revenues_combi, expenses_combi, services_combi, avail_services

def daily_revenues_expenses_menuitem(menu_setup, R, E, Services, avail_services,time_day, Nc, daily_work_hours):
    '''
        Given a setup json structure for the menu, this function returns the 
        time dependent function over [min(time_day), max(time_day)] for the revenues and expenses generated of all 
        combination of sells that can be made given a list of items
        Warning: Mathematically this function only defined for t>1d. Any hourly sales cannot be deduced without adding
                extra knowledge on the daily-time distribution of the buys. 
        R: The revenues for each combination
        E: The expenses for each combination
        Services: The list of services for each combination
        avail_services: The list of services available
        item: The item we are looking for
        Nc: Population (time-dependent function of the number of clients) coming to the restaurant
        time: Time-vector associated to Nc. Must be of same size as Nc
        Returns: 
            - The population revenue R*Nc and expenses E*Nc on a t>daily curve
    '''
    # Verify that the user respect mathematical specifications
    err=check_period_is_modulo_1(time_day)
    if avail_services != menu_setup["service_list"]:
        print("Error: Unrecognized services found. There is a mismatch between the found services and the provided service list")
        print("    available_service determined using each menu item:", avail_services)
        print("    list of services provided in the Json configuration: ", menu_setup["service_list"])
        exit()
    #
    # Perform the Sum to get the total daily revenu
    if menu_setup["limit_by_service"] == False: # THIS CASE ASSUME THAT ALL DISHES ARE SERVED ALL DAY LONG ==> Exposed population is Nc
        return np.sum(R)*Nc, np.sum(E)*Nc
    else: # THIS CASE ASSUME THAT DISHES OF DIFFERENT SERVICES ARE NOT EXPOSING THE SAME POPULATION ==> Exposed population is a Nc * service_time/working_hours
        Rtot=0
        Etot=0
        #Nc_services=np.zeros(len(avail_services))
        for i in range(len(avail_services)):
            Rservice=0
            Eservice=0
            pos=list_indexes(Services, avail_services[i])
            #print('menu_setup["service_time"][i][1] = ', menu_setup["service_time"][i][1])
            #print('menu_setup["service_time"][i][0] = ', menu_setup["service_time"][i][0])
            #print(" daily_work_hours =", daily_work_hours)
            #print(" Ratio: ", (menu_setup["service_time"][i][1]-menu_setup["service_time"][i][0])/daily_work_hours)
            #print('--')
            Nc_services=np.asarray(Nc, dtype=float)*(menu_setup["service_time"][i][1]-menu_setup["service_time"][i][0])/daily_work_hours
            for k in pos:
                Rservice=Rservice + R[k]
                Eservice=Eservice + E[k]
            Rtot = Rtot + Rservice*Nc_services
            Etot = Etot + Eservice*Nc_services
        return Rtot,Etot

# This function is incorrect as it accounts only for a single combination case (1 Client --> 1 item)
# It neglects the fact that clients may take several items: Coffee AND Bacon AND eggs for example
# It is replaced by daily_revenues_expenses_menuitem() that compute the average buys and costs for all
# of the possible combination, provided the daily probability of buy. This function is as well not perfect because
# it neglects many of the conditional probabilities. For example, the probability of buying bacon if you buy eggs is 
# certainly much higher than the probability of buying bacon if you buy a salad. But then accounting for those conditional
# probabilities would be a chalenge as we would need to consider the full tree of conditional probabilities for tens of items
# with little data to support it (unless an exhaustive study has studied those already)
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
'''
def revenue_menuitem(menu_setup, item, time_hours, Nc, return_sale_distrib=False):
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
'''
# This function is incorrect as it accounts only for a single combination case (1 Client --> 1 item)
# It neglects the fact that clients may take several items: Coffee AND Bacon AND eggs for example
# It is replaced by daily_revenues_expenses_menuitem() that compute the average buys and costs for all
# of the possible combination, provided the daily probability of buy. This function is as well not perfect because
# it neglects many of the conditional probabilities. For example, the probability of buying bacon if you buy eggs is 
# certainly much higher than the probability of buying bacon if you buy a salad. But then accounting for those conditional
# probabilities would be a chalenge as we would need to consider the full tree of conditional probabilities for tens of items
# with little data to support it (unless an exhaustive study has studied those already)
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
'''
def expenses_menuitem(menu_setup, item, time_hours, Nc, return_sale_distrib=False, debug=False):
    # Verify that the user respect mathematical specifications
    check_time_is_24h(time_hours, y=Nc)
    #
    R=time_distrib(time_hours-np.min(time_hours), menu_setup["menu_items"][item]["time_distribution"]["name"], menu_setup["menu_items"][item]["time_distribution"]["params"] )
    E=menu_setup["menu_items"][item]["cost"]*R
    debug=True
    if debug == True:
        I=simpson(R, time_hours)
        print("time_hours-np.min(time_hours)  / E ")
        #for i in range(len(E)):
        #    print("{0:.2f}    {1:.2f}   {2:.2f}".format(time_hours[i]-np.min(time_hours), E[i], R[i]))
        #print("--")
        #print("name   : ", menu_setup["menu_items"][item]["time_distribution"]["name"])
        print("params :", menu_setup["menu_items"][item]["time_distribution"]["params"])
        print("Time Integral on [0, 24] for item = {}  : {}".format(item, I))
        print('-')
        #exit()
    if return_sale_distrib == True:
        return E*Nc, E
    else:
        return E*Nc
'''

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
            if work_intervals != []:
                Delta_hours=work_intervals[1] - work_intervals[0] # Total working hours for a single interval (the staff may work 2h on morning, go home and come back 2h in the evening)
                E_staff_day=E_staff_day + Delta_hours*expenses_setup["staff"]["staff_list"][staff_name]["hourly_rate"] # Sum the working hours for all daily working interval
    # Adjust the calculation period, if necessary
    E_staff_day=E_staff_day*period/7
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

    '''
        Function that calculates the revenues and expenses related to
        all the sold products for each day. 
        menu_setup: The Json structure containing all the configuration for the menu
        time_hours: The time vector on which the whole daily configuration is calculated
        Nc : The client population vector. Must be of same size as time_hours
    '''
'''
def revenues_expenses_menuitem_matrix(menu_setup, time_hours, Nc):
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
        service_name=[]
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
            service_name.append(menu_setup["menu_items"][item]["service"])
        tmin=tmax
        tmax=tmax + 24
        time_day.append(day_i)
    time_day=np.asarray(time_day, dtype=float)
    return time_day, R_menu, E_menu, item_name, service_name
'''