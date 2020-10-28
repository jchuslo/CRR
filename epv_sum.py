#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Empirical analysis for various annuitization options

import sys
import glob
import os
import platform
import math
from scipy.optimize import fsolve
import pandas as pd
from pandas import ExcelWriter

import numpy as np

# data_0 = pd.read_excel('data.xlsx')
# mort = data_0['Mortality'].to_numpy()
# RMD = data_0['RMD rule'].to_numpy()

### Step 1. Load data and parameters
# Households financials in the survey data, by single male/female and married couple at age 65
class data:
    dc = 100000
    ssb = 15000
    mort = [0.015899,0.016868,0.018387,0.019092,    0.020462,   0.022047,   0.023816,   0.025697,   0.027674,   0.029828,   0.032382,   0.035360,   0.038579,   0.041991,   0.045724,   0.049974,   0.054971,   0.060902,   0.068009,   0.076327,   0.085749,   0.096120,   0.107306,   0.119231,   0.131905,   0.145375,   0.159718,   0.175027,   0.191392,   0.208919,   0.226082,   0.242533,   0.257903,   0.271821,   0.283929,   0.296581,   0.309802,   0.323618,   0.338056,   0.353144,   0.368912,   0.385389,   0.402610,   0.420607,   0.439416,   0.459073,   0.479618,   0.501090,   0.523533,   0.546989,   0.571506,   0.597132,   0.623916,   0.651913,   0.681177 ]
    mort = np.array(mort)
data_m = data()
# Economic assumptions and Model assumptions
class para:
    inf = math.inf
    inflation = 0.02
    stock_mu = 0.05
    stock_sigma = 0.2
    bond_mu = 0.003
    bond_sigma = 0.07
    af65_m = 0.0660
    af80_m = 0.2020
    gamma = 2
    beta = 0.96
    RMD = [inf,inf,inf,inf,inf,27.4,26.5,25.6,24.7,23.8,22.9,22.0,21.2,20.3,19.5,18.7,17.9,17.1,16.3,15.5,14.8,14.1,13.4,12.7,12.0,11.4,10.8,10.2,9.6,9.1,8.6,8.1,7.6,7.1,6.7,6.3,5.9,5.5,5.2,4.9,4.5,4.2,3.9,3.7,3.4,3.1,2.9,2.6,2.4,2.1,1.9,1.9,1.9,1.9,1.9,1.9]
    RMD = np.array(RMD)
    T = 120-65+1
    N = 1000
para = para()

### Step 2. Monte-Carlo Simulation for market returns
mean = (para.stock_mu, para.bond_mu)
cov = [[para.stock_sigma*para.stock_sigma, 0],[0,para.bond_sigma*para.bond_sigma]]
sim_market = np.random.multivariate_normal(mean, cov, (para.N, para.T))
# Assume 50/50 TDF (portfolio share of stock/bond or risky/risk-free)
sim_real = 0.5 * sim_market[:,:,0] + 0.5 * sim_market[:,:,1]
sim_nominal = sim_real + para.inflation

### Step 3. Run basecase for benchmark
# define strategy structure
class strategy:
    ann_share = 0.4
    ann_age = 65
    ssb_delay = 0
    
# define EPVU function, input (case, data, para, sim_ret, extra) output (epvu, income and wealth stream)
def EPVU(extra, case, data, para, sim_ret, full_output):
    wealth = np.zeros(para.T)
    withdraw = np.zeros(para.T)
    wealth[0] = (1 - case.ann_share) * data.dc + extra
    withdraw[0] = wealth[0] / para.RMD[0]
    # cash flow always at the beginning of period
    for t in range(1,para.T):
        age = 65+t
        wealth[t] = (wealth[t-1] - withdraw[t-1]) * (1+sim_ret[t-1])
        withdraw[t] = wealth[t] / para.RMD[t]
    ann = case.ann_share * data.dc * para.af65_m * np.ones(para.T)
    ssb = data.ssb * np.power((1+para.inflation),range(para.T))
    income = ann + ssb + withdraw
    u = (np.power(income/1000, 1-para.gamma) - 1)/(1-para.gamma)
    surv = 1 - np.append(0,data.mort)
    cumsurv = np.cumprod(surv)
    discount = np.power(para.beta,range(para.T))
    epvu = np.sum(u * discount * cumsurv)
    if full_output is False:
        return(epvu)
    elif full_output is True:
        return(epvu,income,wealth)
# benchmark case
case1 = strategy()    
n = 1
sim_ret = sim_nominal[:,n]
### for testing
sim_ret = [0.076394166,    0.148764296,    0.04594004, 0.040771595,    0.037640085,    0.001241116,    0.032078539,    -0.056608733,   -0.000601594,   0.029950371,    -0.129321449,   0.114973214,    0.059959592,    -0.060152008,   0.143504808,    -0.044883868,   -0.006686335,   0.031466468,    0.127057909,    0.106193956,    0.002239086,    0.058985396,    0.010907306,    0.01607573, 0.064664824,    0.060549801,    0.060487728,    0.059805701,    0.123678668,    0.095334739,    0.031499353,    -0.073431464,   0.021554054,    0.158043786,    0.122251869,    0.042910865,    -0.049985496,   0.035429459,    0.001993554,    -0.094399687,   -0.042330146,   0.016821312,    0.065574681,    0.081887664,    0.077139002,    0.018675923,    0.130242542,    0.104959462,    0.042660472,    0.079135063,    0.122168427,    -0.020227972,   0.140133876,    0.157502018,    0.172325744,    0.039054494]
sim_ret = np.array(sim_ret)
###
full_output = False

epvu1 = EPVU(0,case1,data_m,para,sim_ret,full_output)

### Step 4. Run required equivalent wealth for alternatives, and save the balance and income by age
case2 = strategy()
case2.ann_share = 0.2
epvu2 = EPVU(0,case2,data_m,para,sim_ret,full_output)

extra2 = fsolve(lambda x:EPVU(x,case2,data,para,sim_ret,full_output)-epvu1,0)
### Step 5. Output result
print(epvu1,epvu2,extra2)


# In[ ]:




