#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:34:16 2019

@author: dpg
this code parses the failcase matrix (niters, 8760,168) and extends ANY fail in the generators for a specific
case of (niter, 8760) ---> all the way to the end in the 168 dimension. that is, once the generators
have failed to produce reliability at any time in the 168 hours, the system stays failed.

This condition gets relaxed when energy storage added since stored energy allows system to recover
"""




import numpy as np
from numpy import size
import time
from scipy.special import comb
#from numba import njit
#@njit

def ggp_timestep_bat(g, Pfr_es):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing a single generator
    theprobs = comb(g,g-1)*((1-Pfr_es)**(g-1))*Pfr_es  #equation 8 from ESTCP paper for g-g'=1
    theodds = np.random.rand() #just need a scalar random # here
    res1 = theodds < theprobs #actual matrix of which cases lose a generator
    theresult = g - res1

    return(theresult)
def findcolp_es(usl, bat_time, bat_charge, navail_es, es_max, es_size, Pfr_es):

    arrayshape=usl.shape
    failbatarr = usl*0  # matrix same size as usl but fill with zeros to start
    niters=arrayshape[0]
    for i1 in range(niters):
        print('iteration', i1)
        for i2 in range(8760):
            for t in range(168):
                if t > 0:
                    if usl[i1, i2, t] > 0:  #if unserved load >0, that is, gens NOT ENOUGH to feed load!
                        if (navail_es[i1,i2] > 0) and (es_size  > usl[i1,i2,t ]/max(navail_es[i1,i2],1) ):
                            bat_charge[i1,i2,t] = bat_charge[i1,i2,t-1] - usl[i1,i2,t ]/(navail_es[i1,i2])
                            if bat_charge[i1,i2,t] < 0:
                                failbatarr[i1,i2,t:]=1 # battery failed to cover critical current here and henceforth
                                break
                            navail_es[i1,i2]=ggp_timestep_bat( navail_es[i1,i2], Pfr_es) #knock out battery # available per timestep
                        else:
                            failbatarr[i1,i2,t:]=1 # battery failed to cover critical current here and henceforth
                            break
                    else:  #no unserved load but we can still charge batteries
                        if (navail_es[i1,i2] > 0 and bat_charge[i1, i2, t-1]< es_max ):   #charge battery IF it isn't full
                            charging_current = min(es_size, -usl[i1,i2,t ]/navail_es[i1,i2])
                            bat_charge[i1,i2,t]=bat_charge[i1,i2,t-1]+charging_current
                            bat_charge[i1,i2,t]=min(bat_charge[i1,i2,t], es_max) #cant continue charging once it's full
                            navail_es[i1,i2]=ggp_timestep_bat( navail_es[i1,i2], Pfr_es) #knock out battery after charging
                        else:
                            bat_charge[i1,i2,t]=bat_charge[i1,i2,t-1]  #do nothing, copy full battery charge from previous time!



                else:
                    if usl[i1,i2,t ] > 0:
                        #knock out battery # available per timestep
                        if (navail_es[i1,i2] > 0) and (es_size  > usl[i1,i2,t ]/max(navail_es[i1,i2],1) ):
                            bat_charge[i1,i2,0] = bat_charge[i1,i2,0] - usl[i1,i2,t ]/navail_es[i1,i2]
                            navail_es[i1,i2]=ggp_timestep_bat( navail_es[i1,i2], Pfr_es)
                            if bat_charge[i1,i2,0] < 0:
                                failbatarr[i1,i2,t:]=1 # battery failed to cover critical current here and henceforth
                                break

                        else:
                            failbatarr[i1,i2,t:]=1 # battery failed to cover critical current here and henceforth
                            break




    return(failbatarr)

timestart1 = time.time()
bat_charge = np.zeros((niters,8760, 168)) #track battery charge
bat_charge[:,:,0]=es_max #assume initial battery charge - is FULL
failcasearr1=findcolp_es(usl, bat_time, bat_charge, navail_es, es_max, es_size, Pfr_es)
timestop1=time.time()
print("execution time = %s " , timestop1 - timestart1)
f1=np.mean(failcasearr1,axis=0)
f2=np.mean(f1,axis=0)

colp=1-f2 #the final reliability result