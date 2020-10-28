import sys
import glob
import os
import platform
import pandas as pd
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
import numpy as np

print("current working directory", os.getcwd())
os.chdir(r"C:\Users\Bernard Ho\Desktop\Python Data Analysis")
#datafiles = ["coh0175.219","coh2500.219","coh5024.h19"]
#for datafile in datafiles:
datafile = "coh5024.h19"
df = pd.DataFrame(columns=['Year','Sex','Age','Mortality'])
with open(datafile) as f: lines = f.readlines()
year = 1850
sex = 'male'
for row in lines:
    elements = row.split()
    if len(elements) > 0:
        if elements[0].isdigit():
            age = int(elements[0])
            mort = float(elements[1])
            df = df.append({'Year': year,'Sex':sex,'Age':age,'Mortality':mort}, ignore_index=True)
            if (age == 119) & (sex == 'male'):
                sex = 'female'
            elif (age == 119) & (sex == 'female'):
                sex = 'male'
                year = year + 1

df_male = df[df.Sex=='male']
df_male = df_male.pivot(index='Year',columns='Age')[['Mortality']]
df_female = df[df.Sex=='female']
df_female = df_female.pivot(index='Year',columns='Age')[['Mortality']]
filenamemale = datafile+"m"+".csv"
filenamefemale = datafile+"f"+".csv"
df_male.to_csv(filenamemale)
df_female.to_csv(filenamefemale)
 
