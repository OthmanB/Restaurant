import numpy as np

def check_period_is_modulo_1h(time, regular_dt=True):
    err_codes=[]
    if regular_dt == True:
        dt=time[1] - time[0]
        if (dt - np.floor(dt)) != 0:
            print("Error in check_period_is_modulo_1h(): The time vector is not a multiple of 1h")
            print("        Please ensure that you properly use the this function by setting time[1] - time[0] - np.floor(time[1] - time[0]) = 0")
            print("        Currently dt = time[1] - time[0] = ", dt)
            err_codes.append('not_modulo_1h')
    else:
        i=0
        while (len(err_codes) == 0) and (i<len(time)-1):
            dt=time[i+1] - time[i]
            if (dt - np.floor(dt)) != 0:
                print("Error in check_period_is_modulo_1h(): The time vector is not a multiple of 1h")
                print("        Please ensure that you properly use the this function by setting time[1] - time[0] - np.floor(time[1] - time[0]) = 0")
                print("        Failing to match criteria at dt = time[{}] - time[{}] = {}".format(i+1, i, dt))
                err_codes.append('not_modulo_1h')
            i=i+1
    if len(err_codes) != 0:
        return err_codes
    else:
        return [False]

def check_time_is_24h(time, y=[]):
    '''
        Function that checks that the time is defined over 24h. 
        Optionaly, it can check that another vector has the same size as time
    '''
    err_codes=[]
    if np.max(time) - np.min(time) != 24:
        print("Error in check_time_is_24h():  The time vector provides a time interval that is greater than 24h")
        print("        This is not consistent with the mathematical definition of the tested function")
        print("        Please ensure that you properly use the this function by setting max(time)-min(time) = 24")
        print("        Currently max(time) - min(time) = ", np.max(time) - np.min(time))
        #print("        The program will exit now")
        err_codes.append('not_24h')
    if y != []:
        if len(y) != len(time):
            print("Error in check_time_is_24h():  the time vector has not a consistent size with the optional y-vector")
            print("        This is not consistent with the mathematical definition of the tested function")
            print("        Please ensure that you properly use the code.")
            print("        Currently len(time)={}     !=     len(y) = {}".format(len(time), len(y)))
            #print("        The program will exit now")
            err_codes.append('size_array_mismatch')
    if len(err_codes) != 0:
        return err_codes
    else:
        return [False]

def check_time_is_1y(time, y=[]):
    '''
        Function that checks that the time is defined over 1 year. 
        Optionaly, it can check that another vector has the same size as time
    '''
    err_codes=[]
    if np.max(time) - np.min(time) != 24*365:
        print("Error in check_time_is_24h():  The time vector provides a time interval that is greater than 24h")
        print("        This is not consistent with the mathematical definition of the tested function")
        print("        Please ensure that you properly use the this function by setting max(time)-min(time) = 24")
        print("        Currently max(time) - min(time) = ", np.max(time) - np.min(time), " hours")
        print("        Currently max(time) - min(time) = ", (np.max(time) - np.min(time))/24, " days")
        print("        Currently max(time) - min(time) = ", (np.max(time) - np.min(time))/(24*365), " year")
        #print("        The program will exit now")
        err_codes.append('not_1y')
    if y != []:
        if len(y) != len(time):
            print("Error in check_time_is_24h():  the time vector has not a consistent size with the optional y-vector")
            print("        This is not consistent with the mathematical definition of the tested function")
            print("        Please ensure that you properly use the code.")
            print("        Currently len(time)={}     !=     len(y) = {}".format(len(time), len(y)))
            #print("        The program will exit now")
            err_codes.append('size_array_mismatch')
    if len(err_codes) != 0:
        return err_codes
    else:
        return [False]

def check_time_is_greater_than_period(time, period):
    '''
        Function that check if a given time vector covers a time-span that is greater that a given period
    ''' 
    if (np.max(time) - np.min(time)) < period:
        print("Error in check_time_is_greater_than_period(): The time vector provides a time interval that is smaller than period = ", period)
        print("        Please ensure that you properly use the this function by setting max(time)-min(time) > period")
        print("        Currently max(time) - min(time) = ", np.max(time) - np.min(time)) 
        print("        The program will exit now")
        err=True
    if err == True:
        exit()               