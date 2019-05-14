#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 13 16:44:38 2019

@author: dpg
"""
import numpy as np
import pandas as pd
import genfail_func
import genfail_pv_func
import genfail_pv_func_nunits
from failfind4 import failfind
from pandas import read_excel
from  failfindbat4_func import failfindbat

def readgens(fname):  #reads info from file on diesel gensets, returns unit number & size in a dict object
       ac=read_excel(fname, sheet_name='Diesel Gensets & UPS')
       ack=ac.keys()
       gensize1=ac[ack[2]]  #read gensize from data file
       ngens1 = ac[ack[3]]
       gensize=gensize1[0]  #convert dataframe objects read in from excel into scalars
       ngens=ngens1[0]
       geninfo={'unitnumber': ngens, 'unitsize': gensize}
       return(geninfo)

def bat_availability_start(niters, Pfs_es, n_es ):  #calculates startup availability of battery units
    n_es1 = np.random.rand(niters,8760,n_es)
    navail_es = np.sum(n_es1 > Pfs_es, 2)
    return(navail_es)

fnames = ['NAS Corpus Christi Data for ESTCP Storage Program - Final', \
             'NAS Patuxent River Data for ESTCP Storage Program - Final' , \
             'Fort Bliss Data for ESTCP Storage Program - Final', \
             'Westover ARB Data for ESTCP Storage Program - Final', \
             'March ARB Data for ESTCP Storage Program - Final']

postfix='.xlsx'
# define generator & MCS metrics
niters=40  # # of iterations in MCS
Pfs = 0.002
mtbf = 1700
#define battery metrics
rt_efficiency = 0.7  #round trip battery efficiency... typical for flow batteries
storage_hours=8  # 8 hours of storage per battery but of course anything can be designed in
Pfs_es = 0.015  #as per Ben LaVoie spreadsheet
mtbf_es = 1350 #energy storage MTBF, as per Ben LaVoie spreadsheet
Pfr_es = 1 - np.exp(-1/mtbf_es)
batno=[1, 2] #scenarios with 1 or 2 batteries
gendiffno = [0, -1, -2] #scenarios with 0, -1, -2 generators compared to base case provided by ESTCP
batsizes = [0.5, 1]      #scenarios where batteries are 50% or 100% the size of generator units
scalefacs=[1 , 1.3]     #100% and 130% critical load scenarios
#n_es = 1 #number of energy storage units

#assume each es unit sized same as DG's and has 5 hours capacity
#es_size=750  #power capacity: for here, assume battery size is same as gen unit but it could be anything
#es_max = es_size*8 # total storage energy (hours * power)

for j in range(np.size(fnames)):  #loop through all the individual file names
    fname1=fnames[j]+ postfix        #input file name
    fnameout = fnames[j]+'_out.xlsx' #output file name
    print(fname1, '\n')
# NO PV CASE
    #calculate for each iteration, for each of 8760 possible grid outage times, for each of 168 subsequent time points where # gens don't cover critical load
    failcasearr = genfail_func.readin(fname1, niters, Pfs, mtbf)
    #find out WHERE in the niters x 8760 x 168 timepoints there's a failure and average over iterations, 8760 poss grid outage times
    colp = failfind(failcasearr)
    colp_d = {'Gens Only': colp}  #create dict object from time series result

# PV CASE, NO BATTERIES
    data_in = genfail_pv_func.readin(fname1, niters, Pfs, mtbf,1)#  same calc only ADD PV ARRAY. scalefactor=1 (100% critical load case)
    failcasearr1 = data_in['failcase'] #extract failcase info from result
    #find out WHERE in the niters x 8760 x 168 timepoints there's a failure and average over iterations, 8760 poss grid outage times
    colp1 = failfind(failcasearr1)
    colp_d['Gens and PV Array'] =  colp1 #add additional labels column to output

# obtain diesel genset  info per each military base
    geninfo = readgens(fname1)
    ngens = geninfo['unitnumber']
    nsize = geninfo['unitsize']

# 130% SCENARIO, NO BATTERIES
    data_in = genfail_pv_func.readin(fname1,niters, Pfs, mtbf,1.3)#  same calc only ADD PV ARRAY. scalefactor=1.3 (130% critical load case)
    failcasearr1 = data_in['failcase'] #extract failcase info from result
    #find out WHERE in the niters x 8760 x 168 timepoints there's a failure and average over iterations, 8760 poss grid outage times
    colp1 = failfind(failcasearr1)
    colp_d['Gens and PV Array 130%'] =  colp1 #add additional labels column to output


#   BATTERY SCENARIOS    nested loop thru a. scalefactor, b. # of generators to take out, c. how big the batteries are, d. how many batteries
    for ifuel in range(2):
        print('nofuel ',ifuel,'\n')
        for i0 in range(np.size(scalefacs)):
            print('scalefactor: ',scalefacs[i0], '\n' )
            for i1 in range(np.size(gendiffno)):
                gendiff = gendiffno[i1]
                print('gendiff: ',gendiff, '\n')
                data_in = genfail_pv_func_nunits.readin(fname1,niters, Pfs, mtbf,scalefacs[i0], gendiff, ifuel)#  same calc only ADD PV ARRAY. scalefactor=1 (100% critical load case)
                usl=data_in['usl']
                failcasearr1 = data_in['failcase']
                for i2 in range(np.size(batsizes)):
                    print('batsize ',nsize*batsizes[i2],'\n' )
                    for i3 in range(np.size(batno)):
                        print('batno ',  batno[i3], '\n')
                        es_powercapacity = nsize*batsizes[i2]  #power capacity = fraction of genset size
                        es_energy = es_powercapacity * storage_hours  #energy capacity
                        n_es = batno[i3]
                        navail_es = bat_availability_start(niters, Pfs_es, n_es )
                        print('about to calculate colp\n')
                        colp =failfindbat(usl, navail_es, es_energy, es_powercapacity, rt_efficiency, Pfr_es)
                        print('calculated colp\n')
                        labelstr = 'fuel' + str(ifuel) +' scalefactor ' + str(scalefacs[i0]) + ' genunits' + str(ngens+gendiff) + ' batsize ' + \
                             str(es_powercapacity) + ' bat units ' + str(n_es)

                        colp_d[labelstr]=colp  #concatenate new colp data with new col header, labelstr




    colp_df = pd.DataFrame(colp_d) #create pandas dataframe object from dict... so have header row and key
    colp_df.to_excel(fnameout) #write to excel file

