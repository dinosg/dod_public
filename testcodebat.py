#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: dpg
"""
import os
import numpy as np
import pandas as pd
from pandas import read_excel
from scipy.special import comb
def ggp_timestep(g, Pfr):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing a single generator
    theprobs = comb(g,g-1)*((1-Pfr)**(g-1))*Pfr  #equation 8 from ESTCP paper for g-g'=1
    sg=np.shape(g)
    thearr = np.random.rand(sg[0], sg[1])
    res1 = thearr < theprobs #actual matrix of which cases lose a generator
    theresult = g - res1
    print(np.count_nonzero(res1))
    return(theresult)
    
def ggp_timestep2(g, Pfr):
    #for a vector or matrix of whatever shape containing generator numbers at T, and an instant prob of DOUBLE unit runtime failure
    #Pfr for a SINGLE time step, this time evolves to a matrix of generator numbers at future time T+1
    #
    #only calculates probs of losing TWO generators
    theprobs = comb(g,g-2)*((1-Pfr)**(g-2))*(Pfr**2) #equation 8 from ESTCP paper for g-g'=2
    sg=np.shape(g)
    thearr = np.random.rand(sg[0], sg[1])
    res1 = thearr < theprobs #actual matrix of which cases lose a generator
    theresult = g - 2*res1    #we lose TWO generators here not 1
    print(np.count_nonzero(res1))
    return(theresult)
    

Pfs = 0.002 #from estcp
Pfs_es = 0.015  #as per Ben LaVoie spreadsheet
mtbf=1700 #from estcp
mtbf_es = 1350 #energy storage MTBF, as per Ben LaVoie spreadsheet
niters=40  # # of iterations in MCS
Pfr= 1- np.exp(-1/mtbf)
Pfr_es = 1 - np.exp(-1/mtbf_es)
ngens=7 #hand code # of generators in system, for now
n_es = 2 #number of energy storage units
gensize=750 #hand code this for now
#assume each es unit sized same as DG's and has 5 hours capacity
es_size=750  #power capacity: for here, assume battery size is same as gen unit but it could be anything
es_max = es_size*6 #total storage energy
# step 1.
aa=read_excel('NASCorpusChristi.xlsx', sheet_name='NASCorpusChristi')
zk=aa.keys()
gross_output=aa[zk[1]]
zarr=np.zeros((8760,168))
for u in np.arange(168):
    zarr[:,u]=np.roll(gross_output,-u)
    

ab=read_excel('NASCorpusChristi.xlsx', sheet_name='Critical Loads & Distribution')
abk=ab.keys()
crf=ab[abk[0]]
criticalfrac=crf[0]
cload = zarr * criticalfrac

gens_needed0=np.ceil(cload[:,0]/gensize)
ngens1=np.random.rand(niters,8760,ngens)  #determine # generators that failed to start here
navail=np.sum(ngens1>Pfs,2)    #and generate random #'s
                        #determine # of energy storage units that failed to start here
n_es1 = np.random.rand(niters,8760,n_es) 
navail_es = np.sum(n_es1 > Pfs_es, 2)
print('# of cases w/ 6 gens starting:  ', np.count_nonzero(navail == 6), '\n')
print('#of caes w/ 5 gens starting:  ', np.count_nonzero(navail == 5), '\n')
print('# of caes w/ 4 gens starting:   ', np.count_nonzero(navail == 4), '\n')
print('# of cases w/ 3 gens starting:  ', np.count_nonzero(navail == 3), '\n')
#failcase0 = (gens_needed0 - navail) >0  #initial fails at T=0 (unlikely)
#failcasearr = np.zeros((niters,8760, 168))
#failcasearr[:,:,0] = failcase0.copy() 
usl = np.zeros((niters,8760, 168)) #unserved load



for  t in np.arange(168):  #basic time propagation over 168 hours here
    print('time step ', t, '\n')
    navail1=ggp_timestep(navail,Pfr) #lose a single generator in a single time step
    navail2=ggp_timestep2(navail1,Pfr) #lose 2 gens in a single timestep
    navail=navail2
    gens_neededt = np.ceil(cload[:,t]/gensize)
#    failcasearr[:,:,t] = (gens_neededt - navail)>0
    usl[:,:,t] = cload[:,t]- gensize*navail #calculate unserved load for that timeslice
    
   



