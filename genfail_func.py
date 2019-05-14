#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

This version does NOT subtract PV power production from the gross critical load. Purpose is to duplicate the "variable load" reliability
curves provided by ESTCP. NO BATTERY case or PV.

this reads in the raw excel time series data, the generator size & critical load fraction for the site
and returns the unserved load computed for a matrix (niters x 8760 x 168 ) big. It computes  the # of generators still running after 
t hours (0... 167) where each generator fails at random at each time
step for each iteration. Failures in each iteration are computed separately. Failures are computed stochastically:

a random # is generated between 0 and 1. If that random # is less than Pfs (where Pfs is the numerical probability of a single unit failing to start)
then the generator status = 0, otherwise it's = 1. 

Failure to run is calculated a little differently, using equation 8 from the ESTCP reference. Given g generators running the probability of a single 
generator failing is computed in ggp_timestep. (g' = g -1) If a random number between 0 and 1 < the equation 8 probability of a single generator failing
the number of generators is decremented by one.

Similarly, ggp_timestep2 computes the far lower (but non-zero) probabillty of 2 generators failing in a single timestep. In that case, the # of generators
active is decremented by 2.

# generators required at any time (gens_neededt) is an integer: divide critical load by generator size and round UP.
If this is bigger than the generators available (navail) then we have a reliability FAIL. recorded at time t (of 168) for each iteration and 
possible outage time (of 8760) in matrix failcasearr.
"""

import os
import numpy as np
import pandas as pd
from pandas import read_excel
from scipy.special import comb
from numba import njit

def ggp_timestep(g, Pfr):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing a single generator
    theprobs = g*((1-Pfr)**(g-1))*Pfr  #equation 8 from ESTCP paper for g-g'=1
    sg=g.shape
    thearr = np.random.rand(sg[0], sg[1])
    res1 = thearr < theprobs #actual matrix of which cases lose a generator
    theresult = g - res1
#    print(np.count_nonzero(res1))
    return(theresult)
   
def ggp_timestep2(g, Pfr):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of DOUBLE unit runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing TWO generators
    theprobs = (g*(g-1)/2)*((1-Pfr)**(g-2))*(Pfr**2) #equation 8 from ESTCP paper for g-g'=2
    sg=g.shape
    thearr = np.random.rand(sg[0], sg[1])
    res1 = thearr < theprobs #actual matrix of which cases lose a generator
    theresult = g - 2*res1    #we lose TWO generators here not 1
#    print(np.count_nonzero(res1))
    return(theresult)

def loopthrut(usl, navail, Pfr, cload, gensize):    #not used in this code
    for  t in np.arange(168):  #basic time propagation over 168 hours here
        print('time step ', t, '\n')
        navail1=ggp_timestep(navail,Pfr) #lose a single generator in a single time step
        navail2=ggp_timestep2(navail1,Pfr) #lose 2 gens in a single timestep
        navail=navail2
        usl[:,:,t] = cload[:,t]- gensize*navail #calculate unserved load for that timeslice  
    return(usl)
def readin(file1, niters, Pfs, mtbf):
#    Pfs = 0.002
#    mtbf=1700
#   niters=40  # # of iterations in MCS
    Pfr= 1- np.exp(-1/mtbf)
#    ngens=7 #hand code # of generators in system, for now
    
    # step 1.
#    aa=read_excel('NASCorpusChristi.xlsx', sheet_name='NASCorpusChristi')
    aa=read_excel(file1, sheet_name='Hourly Data')
    zk=aa.keys()
    gross_output=aa[zk[1]]
    pv_power = aa[zk[2]]
  #  gensize=750 #hand code this for now
    cload_shift=np.zeros((8760,168))
    
        
    # step 2.
#    ab=read_excel('NASCorpusChristi.xlsx', sheet_name='Critical Loads & Distribution')
    ab=read_excel(file1, sheet_name='Critical Loads & Distribution')
    ac=read_excel(file1, sheet_name='Diesel Gensets & UPS')
    
    abk=ab.keys()
    ack=ac.keys()
    crf=ab[abk[0]]
   
    gensize1=ac[ack[2]]  #read gensize from data file
    ngens1 = ac[ack[3]]
    gensize=gensize1[0]  #convert dataframe objects read in from excel into scalars
    ngens=ngens1[0]
    criticalfrac=crf[0]
    cload = gross_output * criticalfrac  #the critical load NET of PV power produced
    for u in np.arange(168):  #make the 8760 x 168 array by mapping each of the 8760 time points and shifting them by 0... 167 hours
        cload_shift[:,u]=np.roll(cload,-u)
        
    
    
    gens_needed0=np.ceil(cload_shift[:,0]/gensize)
    ngens1=np.random.rand(niters,8760,ngens)  #determine # generators that failed to start here
    navail=np.sum(ngens1>Pfs,2)    #and generate random #'s
    failcase0 = (gens_needed0 - navail) >0  #initial fails at T=0 (unlikely)
    failcasearr = np.ndarray((niters,8760, 168))
    failcasearr[:,:,0] = failcase0.copy() #copy initial fails into T=0 timepoint
    
    #step 4.
    for  t in np.arange(168):  #basic time propagation over 168 hours here
        print('time step ', t, '\n')
        navail1=ggp_timestep(navail,Pfr) #lose a single generator in a single time step
        navail2=ggp_timestep2(navail1,Pfr) #lose 2 gens in a single timestep
        navail=navail2
        gens_neededt = np.ceil(cload_shift[:,t]/gensize)
        if t > 0:
            failcasearr[:,:,t] = (gens_neededt - navail)>0
        elif t == 0: #treat t=0 case separately b/c you could have a fail to start here too
            failcasearr[:,:,t] = np.logical_or((gens_neededt - navail)>0, failcase0 )
     
    return(failcasearr)
    
    
    
    
    
    
