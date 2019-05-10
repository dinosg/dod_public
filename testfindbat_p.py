#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:34:16 2019

@author: dpg

PARALLEL PROCESSING VERSION. p=Pool()  - here is the # of cores
this code parses the failcase matrix (niters, 8760,168) and extends ANY fail in the generators for a specific
case of (niter, 8760) ---> all the way to the end in the 168 dimension. that is, once the generators
have failed to produce reliability at any time in the 168 hours, the system stays failed.

This condition gets relaxed when energy storage added since stored energy allows system to recover
"""




import numpy as np
from numpy import size
import time
from multiprocessing import Pool

#from numba import njit
#@njit

def ggp_timestep_bat(g, Pfr_es):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing a single generator
    theprobs = comb(g,g-1)*((1-Pfr_es)**(g-1))*Pfr_es  #equation 8 from ESTCP paper for g-g'=1
    sg=np.shape(g)
    theodds = np.random.rand()
    res1 = theodds < theprobs #actual matrix of which cases lose a generator
    theresult = g - res1

    return(theresult)


def findcolp_es_par(i1, i2, usl, navail_es, Pfr_es, es_size, es_max, bat_charge, failbatarr):
    for t in range(168):
        if t > 0:
            if usl[t] > 0:

                if (navail_es > 0) and (es_size  > usl[t]/navail_es ):
                    bat_charge[t] = bat_charge[t-1] - usl[t ]/(navail_es)
                    if bat_charge[t] < 0:
                        failbatarr[t:]=1
                        break
                    navail_es=ggp_timestep_bat( navail_es, Pfr_es) #knock out battery # available per timestep
                else:
                    failbatarr[t:]=1 # battery failed to cover critical current here and henceforth
                    break
            else:
                if (navail_es > 0 and bat_charge[t-1]< es_max):   #charge battery IF it isn't full
                    charging_current = min(es_size,-usl[t]/navail_es)
                    bat_charge[t]=bat_charge[t-1]+charging_current
                    bat_charge[t]=min(bat_charge[t], es_max) #cant continue charging once it's full
                    navail_es=ggp_timestep_bat( navail_es, Pfr_es) #knock out battery after charging
                else:
                    bat_charge[t]=bat_charge[t-1] #copy full battery charge from previous time slot!
        else:
            if usl[t] > 0:

                if (navail_es > 0) and (es_size  >  usl[t]/navail_es ):
                    bat_charge[0] = bat_charge[0] - usl[t]/navail_es
                    if bat_charge[0] < 0:
                        failbatarr[t:]=1
                        break
                    navail_es=ggp_timestep_bat( navail_es, Pfr_es) #knock out battery # available per timestep
                else:
                    failbatarr[t:]=1 # battery failed to cover critical current here and henceforth
                    break

    return i1, i2, navail_es, bat_charge, failbatarr

def findcolp_es(usl, bat_time, bat_charge, navail_es, es_max, es_size, Pfr_es):

    arrayshape=usl.shape
    failbatarr = usl*0  # matrix same size as usl but fill with zeros to start
    niters=arrayshape[0]
#    niters = 5

    p = Pool(40)
    updated_vals = p.starmap(findcolp_es_par, [(i1, i2, usl[i1,i2,:], navail_es[i1,i2], Pfr_es, es_size, es_max, bat_charge[i1,i2,:], failbatarr[i1,i2,:]) for i1 in range(niters) for i2 in range(8760)])
    for i1, i2, navail_es_updated, bat_charge_updated, failbatarr_updated in updated_vals:
        navail_es[i1,i2] = navail_es_updated
        bat_charge[i1,i2,:] = bat_charge_updated
        failbatarr[i1,i2,:] = failbatarr_updated

    return(failbatarr)

timestart1 = time.time()

bat_charge = np.zeros((niters,8760, 168)) #track battery charge
bat_charge[:,:,0]=es_max #assume initial battery charge - is FULL
#bat_time=np.zeros((niters,8760,168))
bat_time=0
failcasearr1=findcolp_es(usl, bat_time, bat_charge, navail_es, es_max, es_size, Pfr_es)
timestop1=time.time()
print("execution time = " , timestop1 - timestart1)
f1=np.mean(failcasearr1,axis=0)
f2=np.mean(f1,axis=0)

colp=1-f2 #the final reliability result
