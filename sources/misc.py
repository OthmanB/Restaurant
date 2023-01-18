import numpy as np
from scipy.integrate import simpson

def list_indexes(list_in, s):
    '''
        Search the string s into the list list_in and
        return all indexes where the occurence happened
    '''
    matched_i = []
    N = len(list_in)
    i = 0
    while i < N:
        if s == list_in[i]:
            matched_i.append(i)
        i = i + 1 
    return matched_i

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

def step(list_input, k, result=[]):
    '''
        Recursive function that is used to determine all of the combination of a 
        tree of combination between elements of a list
        list_input: The input vector of elements for which we want to the combinations
        k: An index for the depth at which we compute the branches. k=0 is the root branch. k=len(list_input) are the leafs
        result: An array used for the recursion. At first execution, it must be empty []. At the end of the recursion, it has the results.
    '''
    # last recursion
    if k == 0:
        return result

    # First recursion (when result ==[]), start with the single solutions (a, b, c, ...) in result
    if (len(result) == 0):
        for i in list_input:
            subList=[]
            subList.append(i)
            result.append(subList);
            #result.append(list_input[i])
        # Around we go again. 
        return step(list_input, k - 1, result)
    #
    # Cross result with input.  Taking us to 2 entries per sub list.  Then 3. Then... 
    newResult =[]
    for subList in result:
        for i in list_input:
            newSubList=[]
            for s in subList:
                newSubList.append(s);
            newSubList.append(i);
            newResult.append(newSubList);
    # Around we go again.  
    return step(list_input, k - 1, newResult)

def combinations(in_vec, without_recurence=False):
    '''
        Make lists of all possible combinations using the in_vec list entries
        in_vec: The list of elements for which combinations are looked for
        without_recurrence: If False, keep all recurrence by permutation (eg. [1,2] and [2,1]).
            Otherwise, remove duplicates ([[1,2], [2,1] --> [[1,2]])  
    '''
    if without_recurence == False:
        return step(in_vec, len(in_vec), result=[])
    else:
        r=step(in_vec, len(in_vec), result=[])
        return rem_duplicates(r)

def rem_duplicates(list_in, sorting=True, algo='comprehension'):
    '''
        Take a list and remove duplicates
        list_in: The list from which duplicates are to be removed
        sorting: If true, it removes elements that appear in any kind of order eg. :
            - [1,2] and [2,1] are the same and whatever is the first in order, it will be removed
            - ['Bacon', 'Egg'] and ['Egg', 'Bacon'] are the same  and whatever is the first in order, it will be removed
    '''
    if algo != 'comprehension' and algo != 'for1' and algo != 'for2':
        print('Warning: Unrecognized algo type.')
        print("         Please use:")
        print("                - 'comprehension' : Make use of compherension list. This is the most compact")
        print("                - 'for1' : Make use of a single for loop with a not in statement")
        print("                - 'for2' : Make use of two for loops. This is the most robust when dealing with strings")
        print("         Pursuing with the default algo: comprehension")
        algo='comprehension'
    #
    list_out= []
    if algo == 'comprehension':
        if sorting == True:
            [list_out.append(sorted(item)) for item in list_in if sorted(item) not in list_out]
        else:
            [list_out.append(item) for item in list_in if item not in list_out]
    if algo == 'for1':
        for item in list_in:
            if sorting == True:
                if sorted(item) not in list_out:
                    list_out.append(sorted(item))
            else:
                if item not in list_out:
                    list_out.append(item)     
    if algo == 'for2':  
        list_out=[]
        for item in list_in:
            put=True
            for i in range(len(list_out)):
                if item  == list_out[i]:
                    put=False
            if put == True:       
                list_out.append(item)
    return list_out


def deep_rem_duplicates(list_in):
    '''
        Remove duplicate down to the level of a list of list, including permutations
    '''
    list_u=[]
    # Remove sub-elements that appear multiple times. This will create lists of different lengths
    for sublist in list_in:
        r=rem_duplicates(sublist, sorting=False)
        list_u.append(r)
    # Remove the remaining duplicates by also removing permutations
    list_unique=rem_duplicates(list_u, sorting=True)
    return list_unique
