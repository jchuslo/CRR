#!/usr/bin/env python
# coding: utf-8

# In[3]:


# Update Annuity Market Loads (Money's Worth) in Mitchell, Poterba, Warshawsky, and Brown (1999)
# Last modifed by JC August 9 2019
get_ipython().run_line_magic('reset', '-f')

import numpy as np
import pandas as pd
import itertools
from openpyxl import load_workbook
import os as os
from os.path import expanduser as ospath

# Step 1. Load data
# Annuity market quotes from immediateannuity.com at August 1st
keys = ['sex','age','IA/DA','COLA','payout']

data2 = pd.read_excel(ospath('~/Desktop/work/projects/wenliang_proj/MW/MW_annuity_data.xlsx')) # DIRECTORY

data2 = data2[['Gender','Age','Type','COLA','Payout Ratio']]
data2.columns = ['sex','age','IA/DA','COLA','payout']
data2.loc[data2['sex'] == 'Male', 'sex'] = 'man'
data2.loc[data2['sex'] == 'Female', 'sex'] = 'woman'
data2.loc[data2['IA/DA'] == 'Immediate', 'IA/DA'] = 'IA'
data2.loc[data2['IA/DA'] == 'Deferred', 'IA/DA'] = 'DA'
data = data2
market_quote = pd.DataFrame(data,columns = keys)

# Life table: general population from SSA cohort, annuitant from SOA
#USE CUSTOM DIRECTORY

SSA_table_m = pd.read_excel('Cohort.xlsx',sheet_name='male',index_col=0,header=0)
SSA_table_f = pd.read_excel('Cohort.xlsx',sheet_name='female',index_col=0,header=0)
SOA_table_m = pd.read_excel(ospath('~/Desktop/work/projects/wenliang_proj/MW/2012_SOA_mort.xlsx'),sheet_name='male',index_col=None,header=0)
SOA_table_f = pd.read_excel(ospath('~/Desktop/work/projects/wenliang_proj/MW/2012_SOA_mort.xlsx'),sheet_name='female',index_col=None,header=0)
SOA_table_m = SOA_table_m[['mort','scalar']]
SOA_table_f = SOA_table_f[['mort','scalar']]

tbill = pd.read_excel(ospath('~/Desktop/work/projects/wenliang_proj/MW/tbill_impute.xlsx'),sheet_name='spot_rate',index_col=None,header=None) # DIRECTORY

tbill = tbill.to_numpy()

lifetable = {'SSA':{'male':SSA_table_m,'female':SSA_table_f}, 'SOA':{'male':SOA_table_m['mort'],'female':SOA_table_f['mort']}}
scalar = {'male':SOA_table_m['scalar'],'female':SOA_table_f['scalar']}
# interest rate: Treasury bond by term structure or Corporate bond
interest_rate = {'gov':tbill,'baa':0.0428,'aaa':0.0329} #gov_r=0.0206
# other economic factors
inf = 0.02 # inflation
RMD = {55:0,60:0,65:0,70:0,75:0,80:0,85:0}
tax_rate = 0.3

# Step 2. Core calculation
# define money's worth calculation: assume cash flow at the end of period
def MW_IA(sex,age,product,cola,payout,population,r_type,tax):
    # if before tax
    T = 120-age
    if population == 'general':
        mort = lifetable['SSA'][sex]
        if product == 'IA':
            byear = 2019 - age
            q = np.array(mort.loc[byear])
            q = q[age:]
            pmt = payout * np.ones(T)
            cumsurv = np.cumprod(1-q)
        else:
            byear = 2019 - 65
            q = np.array(mort.loc[byear])
            q = q[age:]
            pmt = payout * np.array([0]*(85-65)+[1]*(T-20))
            cumsurv = np.cumprod(1-q)
        if r_type == 'Treasury bond':
#             r = interest_rate['gov'] * np.ones(T)
            r= interest_rate['gov'][0:T]
            discount = np.cumprod(1/(1+r))
        elif r_type == 'AAA Corporate':
            r = interest_rate['aaa'] * np.ones(T)
            discount = np.cumprod(1/(1+r))
        else:
            r = interest_rate['baa'] * np.ones(T)
            discount = np.cumprod(1/(1+r))
        if tax == 'before': #needs 'after'
            mw = np.sum(pmt * cumsurv * discount)
        else:
            mw = np.sum(pmt * cumsurv * discount)
        return(mw)
    elif population == 'annuitant':
        if product == 'IA':
            mort = np.zeros(shape=(T,1))

            for i in range(0,T-1):
                mort[i] = (lifetable['SOA'][sex][age+i])*((1-scalar[sex][age+i])**(7+i))

            pmt = payout * np.ones(T)
            cumsurv = np.cumprod(1-mort)
        else:
            mort = np.zeros(shape=(T,1))

            for i in range(0,T-1):
                mort[i] = (lifetable['SOA'][sex][age+i])*((1-scalar[sex][age+i])**(7+i))

            pmt = payout * np.array([0]*(85-65)+[1]*(T-20))
            cumsurv = np.cumprod(1-mort)
        if r_type == 'Treasury bond':
#             r = interest_rate['gov'] * np.ones(T)
            r=interest_rate['gov'][0:T]
            discount = np.cumprod(1/(1+r))
        elif r_type == 'AAA Corporate':
            r = interest_rate['aaa'] * np.ones(T)
            discount = np.cumprod(1/(1+r))
        else:
            r = interest_rate['baa'] * np.ones(T)
            discount = np.cumprod(1/(1+r))
            
        if tax == 'before': #needs 'after'
            mw = np.sum(pmt * cumsurv * discount)
        else:
            mw = np.sum(pmt * cumsurv * discount)
        return(mw)
    else:
        return('ERROR: Please choose "general" or "annuitant" as a population setting')

# Step 3. Run all cases
keys = ['sex','population','int_rate','tax']
sex = ['man','woman']
population = ['general','annuitant']
int_rate = ['Treasury bond','AAA Corporate','BAA Corporate']
tax = ['before', 'after']
combo = list(itertools.product(sex, population,int_rate,tax)) #RUNS ALL POSSIBLE CASES
testing = pd.DataFrame(combo,columns = keys)
result = market_quote.merge(testing,how='outer',on = 'sex')
result.index = np.arange(1, len(result)+1)
runs = result.to_dict(orient='records')

runs = pd.DataFrame(data=runs)
runs.loc[runs['sex'] == 'man', 'sex'] = 'male'
runs.loc[runs['sex'] == 'woman', 'sex'] = 'female'
runs['MW'] = ""

runs['MW'] = np.vectorize(MW_IA)(runs['sex'],runs['age'],runs['IA/DA'],runs['COLA'],runs['payout'],runs['population'],runs['int_rate'],runs['tax'])

#Choose only maximum payout from each product

max_payout = pd.Series([chunk.max() for chunk in np.array_split(data2['payout'], 48)])
runs_max = runs[runs['payout'].isin(max_payout)]


# Step 4. Print Results/save to csv

runs_max.to_csv(ospath('filepath/runs.csv'))

# # Pivot table

# table = pd.pivot_table(runs_max[(runs_max['age']==55) | (runs_max['age']==65) | (runs_max['age']==75)], values='MW', index=['sex','age'], columns=['population','int_rate'])
# print(table)


# In[ ]:




