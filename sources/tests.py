import matplotlib.pyplot as plt
import numpy as np
from functions_population import daily_base_fct
from functions_population import weekly_fct
from functions_population import yearly_fct
from functions_population import compute_Nc
from functions_income import *
from error_checks import *
from scipy.integrate import simpson
from misc import combinations,rem_duplicates, deep_rem_duplicates
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

# ----

def test_combinations():
    print(' Small test with simple lists...')
    in_vec=['Bacon','Eggs']
    r=combinations(in_vec)
    for i in r:
        print(i)
    print('--')
    r=combinations(in_vec, without_recurence=True)
    finallist=[]
    for sublist in r:
        finallist.append(rem_duplicates(sublist, sorting=False))
    for i in finallist:
        print(i)
    print(' Done.')
    print(' Simple test with lists of lists...')
    in_vec=[['Bacon', 1],['Eggs', 0.5]]
    r=combinations(in_vec)
    for i in r:
        print(i)
    print('--')
    r=combinations(in_vec, without_recurence=True)
    finallist=[]
    for sublist in r:
        finallist.append(rem_duplicates(sublist, sorting=False))
    for i in finallist:
        print(i)
    print('Done.')

#names=["Bacon", "Eggs", "Bread"]
#proba=[0.5, 0.5, 0.5]
#price=[10, 5, 1]
#cost=[3, 1, 0]
names=["Bacon", "Eggs", "Bread", "Donuts", "Main_Dish", "Sushi", "Coffee"]
proba=[0.5,      0.5,    0.5,      0.5,      0.5,          0.5 ,    0.2   ]
price=[10,       5,       5,       5 ,        5   ,        5   ,    5     ]
cost=[3,         1,       1,       1,        1    ,        1    ,   1     ]

l=[]
for i in range(len(names)):
    l.append([names[i], proba[i], price[i], cost[i]])
combi_all=combinations(l, without_recurence=True)
combi_unique=deep_rem_duplicates(combi_all)
print('-- Unique Combination --')
for c in combi_unique:
    print(c)

# Compute the revenue and costs for each combinations
revenues_combi=[]
expenses_combi=[]
for c in combi_unique:
    proba_joint=1
    price_paid=0
    price_cost=0
    for cc in c:
        proba_joint=proba_joint*cc[1]
        price_paid=price_paid + cc[2]
        price_cost=price_cost + cc[3]
    revenues_combi.append(proba_joint*price_paid)
    expenses_combi.append(proba_joint*price_cost)
print(revenues_combi)

for i in range(len(combi_unique)):
    print("[", i, "] Combi: ", combi_unique[i])
    print( "   revenues_combi = ", revenues_combi[i] )
print("Total revenues:")
print(np.sum(revenues_combi))
