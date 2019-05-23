#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  7 14:34:16 2019

@author: dpg
Generator only case for reproducing ESTCP 'variable load' curves. 
this code parses the failcase matrix (niters, 8760,168) and extends ANY fail in the generators for a specific
case of (niter, 8760) ---> all the way to the end in the 168 dimension. that is, once the generators
have failed to produce reliability at any time in the 168 hours, the system STAYS failed. 

(This condition gets relaxed when energy storage added since stored energy allows system to recover)

Version used accelerator package numba. Module njit from numba compiles modules pre-fixed with @njit, compiles then runs in
C and vectorizes for performance enhancement minutes --> seconds. see https://numba.pydata.org
"""




import numpy as np
from numpy import size
import time

from numba import njit
@njit
def findcolp1(failcasearr):
    arrayshape=failcasearr.shape
    niters=arrayshape[0]
    qi=np.zeros((niters,8760))
    for i1 in range(niters):
        for i2 in range(8760):
            qz=np.nonzero(failcasearr[i1,i2,:])
            qz0=qz[0]
            qz1=failcasearr[i1,i2,:]
            if np.sum(qz1 ) > 0:  #go here IF AND ONLY IF there's at least 1 fail during the 168 hours
                qi[i1,i2]=qz0[0]
                failcasearr[i1,i2,qz0[0]:]=1  #fail REMAINDER OF ALL THE HOURS AFTER THE INITIAL FAIL
#            else:
#                print(qz0 == [])
#compute failure statistics by averaging over 8760 possible initial grid disconnect hours and MCS cases
    #f1=np.mean(failcasearr,axis=0)
    #f2=np.mean(f1,axis=0)
    #f2=1-f2  #reliability = 1 - failure probability. f2 is the FINAL RESULT
    return(failcasearr)
def failfind(failcasearr)  :  
    timestart1 = time.time()
    failcasearr1=findcolp1(failcasearr)
    timestop1=time.time()
    print("execution time = %s " , timestop1 - timestart1)
    colp=np.mean(failcasearr1, axis=0)
    colp=np.mean(colp, axis=0)
    colp=1-colp
    return(colp)
