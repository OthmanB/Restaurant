import numpy as np
from scipy.integrate import quad
import matplotlib.pyplot as plt

def A_fct(nr):
    '''
        Definition of the function for the attractiveness factor 
        nr: number of competitors
    '''
    return 1/(nr+1)

def Influence_fct(r, Reff, r0=0):
    '''
        Definition of the influence function in radial coordinates. 
        This function assumes that the terrain (routes, hills, slopes,...)
        has no effect on the propension for people to reach the restaurant
        r: radial distance to the center r0
        Reff: effective radius of influence of the restaurant
        r0 (optional): position of the restaurant (default, center)
    '''
    I= np.exp(-r**2 / (2* Reff**2))/np.exp(0)
    return I
    
def Nliving(rho, Reff):
    '''
        Definition of the maximum number of people living in the restaurant surroundings succeptible to get into the restaurant
        within the effect radius
        rho: local population density
        Reff: Effect radius of influence of the restaurant
    '''
    Nliving = 2*np.pi * Reff**2 * rho / np.exp(0)
    return Nliving

def Nworking(Nworkers, Nworkers_living, r, Reff):
    '''
        Definition of the maximum number of workers that potentially can eat in the restaurant
        Nworkers: List/Array of number of workers within the area of influence of the restaurant
        Nworkers_living: List/Array of number of workers that live within the area of influence
        r: List/Array giving the radial distance between the working place and the restaurant
    '''
    N=len(Nworkers)
    if N != len(Nworkers_living) and N != len(r):
        print('Error: The sizes of Nworkers, Nworkers_living and r are not the same')
        print('       Returning -1')
        return -1
    Nwork=0
    for i in range(N):
        Nwork=Nwork + (Nworkers[i] - Nworkers_living[i]) * Influence_fct(r[i], Reff)
    return Nwork

def manyGauss_fct(x, params, x_truncate=[]):
    '''
        A model with many summed Gaussians.  
        x: The value at which the gaussian is evaluated
        params: List of lists. Each element of the top-level list describe one Gaussian. Each sublist must
                have 3 parameters: (0) A height, (1) mean and (2) standard deviation
        x_truncate: 2-elements array/list. If defined, returns 0 below/above the min/max values
    '''
    r=0
    for p in params:
        r=r + p[0]*np.exp(-(x-p[1])**2/(2*p[2]**2))
    if len(x_truncate) == 2:
        f=np.where(np.bitwise_and(x < x_truncate[0], x > x_truncate[1]))[0]
        if f != []:
            r[f]=0
    return r

def Norm_manyGauss_fct(params, x_truncate=[], range_int=[0,24], limit_precision=1e-3):
    '''
        Compute the integral of manyGauss_fct().
        params: The parameters as defined in manyGauss_fct()
        range_int: The range on which the integral is performed
        limit_precision: If the precision start to be lower than limit_precision, shows a warning message
    '''
    Norm=quad(manyGauss_fct, range_int[0], range_int[1], args=(params, x_truncate))
    if Norm[1] > limit_precision:
        print("Warning: precision = ", Norm[1], " is above limit =", limit_precision, " for Norm_manyGauss_fct")
    return Norm[0]

def daily_base_fct(hour, params, normalise=True, working_hours=[7, 21]):
    '''
        Function describing the daily base modulation due to social behavior (eg. 3 meals/day). Called B(t|p) in the docs.
        This function is a sum of functions, each defined by a time origin, a time interval and
        is normalised to 1 using its integral if requested. This function DOES NOT account for day-to-day variation over
        the week or over the year (this is performed by weekly_fct() and yearly_fct())
        hour: Time of the day in hours. Must be an array. If it is not, it will be converted into one
        params: List of lists. Each element of the top-level list describe one function. Each sublist must
                have 3 parameters, as defined in manyGauss_fct(). 
                Units must be in hours
                example: [[1, 7, 0.5]], generate one gaussian of relative height 1, centered at hour = 7
                with a width of 0.5 hours.
        normalise: If set to True, normalise the function by it's integral. If one assumes that a customer comes only
        at maximum once a day, this should be set to True (which is the default assumption here).
        working_hours (default 7h - 21h): time of the day in hours during which the restaurant is open
    '''
    try:
        l=len(hour)
    except:
        hour=np.asarray([hour], dtype=float)
    #
    B=manyGauss_fct(hour, params, x_truncate=working_hours)
    # Normalise by the integral by performing a quadratic integration of [0, 24h]
    if normalise == True:
        Norm=Norm_manyGauss_fct(params, x_truncate=working_hours)
        return B/Norm
    else:
        return B


def weekly_fct(setup, weekly_day="all"):
    '''
        Function that describes the weekly behavior of the people.
        The function calls daily_base_fct() and calibrates the heights of the Gaussian
        based on the setup configuration (loaded beforehand by reading a json config file)
        Note that there is two truncations for different reasons:
            - First, we truncate over the maximum number of working hours of all of the restaurants around (e.g. [7, 21]). 
                     THIS FUNCTION IS NORMALISED BY THE INTEGRAL ==> We get the maximum potential number of people that 
                     may come, knowing that there is competition at these time interval
            - Then, we truncate the function at the RESTAURANT working hours. THIS IS NOT NORMALISED. ==> We get the number of people 
                     That were planing to eat on the opening hours of the restaurant. The truncation effectively remove people that 
                     were not planing to come anyway due to a conflicting agenda.
            The rational is that all people will look for food. But because some restaurant may open longer than ours,
            we mecanically cannot compete with them when we are closed. So we loose that part of the potential clients, which 
            reduces the total reservoir of available people.
        setup: Json configuration regarding the proportion of people that are expected at any given moment of the year using gaussian sums. 
        weekly_day: Either
            - "all": Put weekends and weekdays
            - "weekday": Only weekdays
            - "weekend": Only weekends 
            This is used to separate the Working population (that will not work and therefore eat at the places on weekends) from the living population
    '''
    # --- Parameters definition over a day and over a week ---
    Npts_24h=int(np.ceil(24./setup["model_resolution"]))
    hours=np.linspace(0, 24., Npts_24h + 1) # in hours
    time=np.linspace(0, 24*7., 7*Npts_24h + 1)# The weekly timeserie is in hours
    afluence=np.zeros(7*Npts_24h + 1)
    if weekly_day != "weekdays" and weekly_day != "weekends" and weekly_day != "all":
        print("Error: Unrocognized keyword weekly_day = ", weekly_day)
        print("       Debug required. The program will exit now")
        exit(-1)
    #
    # --- For each day, generate the Base function for the daily afluence and append it to the weekly timeseries ---
    xmin=0
    xmax=Npts_24h
    for day in setup['reference']:
            if weekly_day == "weekdays" or weekly_day == "all":
                if day != "Saturday" and day != "Sunday":
                    #print("day =", day)             
                    B=daily_base_fct(hours, setup['reference'][day]["daily_distributions"], normalise=True, working_hours=setup['reference'][day]["working_hours"])
                    # -- Truncate the Daily base function to account for the restaurant working hours --
                    posnull=np.where(np.bitwise_or(hours <= setup["restaurant"][day]["working_hours"][0], hours >= setup["restaurant"][day]["working_hours"][1]))[0]
                    B[posnull]=0
                    # -- accolate daily elements to the weekly curve --           
                    afluence[xmin:xmax]=B[0:-1]
            if weekly_day == "weekends" or weekly_day == "all":
                if day == "Saturday" or day == "Sunday":
                    #print("day =", day)
                    B=daily_base_fct(hours, setup['reference'][day]["daily_distributions"], normalise=True, working_hours=setup['reference'][day]["working_hours"])
                    # -- Truncate the Daily base function to account for the restaurant working hours --
                    posnull=np.where(np.bitwise_or(hours <= setup["restaurant"][day]["working_hours"][0], hours >= setup["restaurant"][day]["working_hours"][1]))[0]
                    B[posnull]=0
                    # -- accolate daily elements to the weekly curve --           
                    afluence[xmin:xmax]=B[0:-1]
            xmin=xmax
            xmax=xmin + Npts_24h
    return time, afluence
   
def yearly_modulation(setup, time, unit='hour'):
    '''
        The function that creates the modulation of the restaurant activity in function of the time of the year
        setup: Json configuration regarding the proportion of people that are expected at any given moment of the year using gaussian sums.
        time: A time vector on which we construct the modulation curve. The 0 must be set to 01-Jan
        unit: Unit of time. Either 'year' or 'hour'. Allows to control the x-axis units. 
    '''
    if unit == "hour": # We convert into years because the yearly function has parameters given in years
        t_compute = time/(365.*24.)
    if unit != "hour" and unit != "year":
        print("Error in yearly_modulation: You need to specifiy unit as either 'hour' or 'year'")
        exit()
    #
    if setup["yearly_function"]["func"] == "default":
        #Npts_24h=int(np.ceil(24/setup["model_resolution"]))
        #Npts_1y=Npts_24h*365
        Amp_max=setup["yearly_function"]["params"][0]
        Dy=setup["yearly_function"]["params"][1]
        Period=setup["yearly_function"]["params"][2]
        phase=setup["yearly_function"]["params"][3]
        #time=np.linspace(0,1, Npts_1y + 1)
        model=Amp_max- Dy*np.cos(2*np.pi*t_compute/Period + phase)
    else:
        print("Error: Type of function used for the yearly modulation not recognized:", setup["yearly_function"]["func"])
        print("       Supported function(s):")
        print("             - default")
        print("The program will exit now")
        exit(-1)
    return time, model

def yearly_fct(setup, weekly_day="all"):
    '''
        Function that implements effects of the social weekly behavior (week ends have higher afluence than on week days)
        and that incorporate seasonal modulation using a sinusoidal function to get the yearly afluence. As the weather would require a constant feed
        using an API with local weather services, the weather is neglected here.
        setup: The setup as it is read from the behavior json file
        weekly_day: Either
            - "all": Put weekends and weekdays
            - "weekday": Only weekdays
            - "weekend": Only weekends 
    '''
    # --- Compute the weekly model ---
    time_w, afluence_w=weekly_fct(setup, weekly_day=weekly_day)
    Npts_w=len(time_w)
    Nweeks=53 # There is 52.142857 weeks in a year. We calculate over 53 and we will truncate the excess later. 
    #
    # --- Compute the yearly model over 53 weeks by repeating the weekly pattern --
    #     There is some tricky stuff here due to the fact that 0h and 24h is the same in virtue of the periodicity of the function
    #     We basically need to copy points without counting the duplicate at h=0 and h=24. 
    #     Then we need to add the last point at t = 24h * 53w
    model=np.zeros(Nweeks*Npts_w  - Nweeks + 1)
    time_m=np.linspace(0, Nweeks*7*24, Nweeks*Npts_w - Nweeks + 1)
    p0=0
    p1=Npts_w -1
    for k in range(Nweeks):
        model[p0:p1]=afluence_w[0:-1]
        p0=p1
        p1=p0+Npts_w - 1
    model[-1]=afluence_w[-1]
    # --- Compute the yearly modulation over 365 days = 52.1428 weeks ---
    time_y, modulation=yearly_modulation(setup, time_m, unit='hour')
    posOK=np.where(time_m <= 365*24)[0] # This is to remove the extra few days that may arise from the 53 weeks rounding
    time_y=time_y[posOK]
    model_f=model[posOK]*modulation[posOK]
    return time_y, model_f

    
def compute_Nc(behavior_setup, population_setup):
    '''
        Computation of the number of clients as a function of the time within a year
        behavior setup: Json configuration regarding the proportion of people that are expected at any given moment of the year using gaussian sums.
        population_setup: Json configuration to compute the population that is within reach of the restaurant and willing to eat there
    '''
    time, WY_model_week=yearly_fct(behavior_setup, weekly_day="weekdays")
    time, WY_model_weekend=yearly_fct(behavior_setup, weekly_day="weekends")
    A=A_fct(population_setup['attractiveness']['nr'])
    Reff=population_setup['Nliving']["effective_time_radius"]*population_setup['Nliving']["travel_speed"]/60. # Radius in km
    Nl=Nliving(population_setup['Nliving']['population_density'], Reff) # Density in Number/km^2
    dist=[]
    Np=[]
    Np_living=[]
    for index in population_setup["Nworking"]["places"]:
        dist.append(population_setup["Nworking"]["places"][index]["distance"]*1e-3) # distances converted in km
        Np.append(population_setup["Nworking"]["places"][index]["Nworkers"])
        Np_living.append(population_setup["Nworking"]["places"][index]["Commute_fraction"]*population_setup["Nworking"]["places"][index]["Nworkers"])
    Nw=Nworking(Np, Np_living, dist, Reff) # Number of workers/students that may come (ONLY WEEK DAYS)
    Ntr=population_setup["Ntransit"]["Ntransit"] # Number of people transiting that may come
    weekday_afluence=(Nl+Ntr)*WY_model_week*A
    weekend_afluence=(Nl + Nw + Ntr)*WY_model_weekend*A
    return time, weekday_afluence, weekend_afluence # During the weekdays there is (Nl + Nw + Ntr) people. But only (Nl+Ntr) otherwise