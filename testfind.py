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
qi=np.zeros((niters,8760))
for i1 in range(niters):

  for i2 in range(8760):
      qz=np.nonzero(failcasearr[i1,i2,:])
      qz0=qz[0]
      if size(qz) > 0:  #go here IF AND ONLY IF there's at least 1 fail during the 168 hours
  #        print(i1, i2, qz0[0], '\n')
          qi[i1,i2]=qz0[0]
          failcasearr[i1,i2,qz0[0]:]=1  #fail REMAINDER OF ALL THE HOURS AFTER THE INITIAL FAIL
  
#compute failure statistics by averaging over 8760 possible initial grid disconnect hours and MCS cases
  f1=np.mean(failcasearr,axis=0)
  f2=np.mean(f1,axis=0)
  f2=1-f2  #reliability = 1 - failure probability. f2 is the FINAL RESULT