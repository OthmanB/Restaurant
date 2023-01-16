import numpy as np
from scipy.integrate import simpson

def sums(t, y, Dt):
    '''
        Sum a curve y(t) within a sliding window of width Dt
    '''
    t_new=[]
    y_new=[]
    tmin=0
    tmax=Dt
    t_new_i=0 # The new time, in unit of Dt
    while tmin <= np.max(t):
        posOK=np.where(np.bitwise_and(t >= tmin, t <= tmax))[0]
        y_new.append(np.sum(y[posOK]))
        t_new.append(t_new_i)
        tmin=tmax
        tmax=tmax+Dt
        t_new_i=t_new_i + 1
    return np.asarray(t_new, dtype=float), np.asarray(y_new, dtype=float)


def integrate(t, y, Dt):
    '''
        Integate a curve y(t) within a sliding window of width Dt
    '''
    t_new=[]
    y_new=[]
    tmin=0
    tmax=Dt
    t_new_i=0 # The new time, in unit of Dt
    while tmin <= np.max(t):
        posOK=np.where(np.bitwise_and(t >= tmin, t <= tmax))[0]
        I=simpson(y[posOK], t[posOK])
        y_new.append(I)
        t_new.append(t_new_i)
        tmin=tmax
        tmax=tmax+Dt
        t_new_i=t_new_i + 1
    return np.asarray(t_new, dtype=float), np.asarray(y_new, dtype=float)
