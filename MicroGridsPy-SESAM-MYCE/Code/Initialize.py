"""
MicroGridsPy - Multi-year capacity-expansion (MYCE)

Linear Programming framework for microgrids least-cost sizing,
able to account for time-variable load demand evolution and capacity expansion.

Authors: 
    Giulia Guidicini   - Department of Energy, Politecnico di Milano 
    Lorenzo Rinaldi    - Department of Energy, Politecnico di Milano
    Nicolò Stevanato   - Department of Energy, Politecnico di Milano / Fondazione Eni Enrico Mattei
    Francesco Lombardi - Department of Energy, Politecnico di Milano
    Emanuela Colombo   - Department of Energy, Politecnico di Milano
Based on the original model by:
    Sergio Balderrama  - Department of Mechanical and Aerospace Engineering, University of Liège / San Simon University, Centro Universitario de Investigacion en Energia
    Sylvain Quoilin    - Department of Mechanical Engineering Technology, KU Leuven
"""


import pandas as pd
import re

#%% This section extracts the values of Scenarios, Periods, Years from data.dat and creates ranges for them
Data_file = "Inputs/data.dat"
Data_import = open(Data_file).readlines()

for i in range(len(Data_import)):
    if "param: Scenarios" in Data_import[i]:
        n_scenarios = int((re.findall('\d+',Data_import[i])[0]))
    if "param: Years" in Data_import[i]:
        n_years = int((re.findall('\d+',Data_import[i])[0]))
    if "param: Periods" in Data_import[i]:
        n_periods = int((re.findall('\d+',Data_import[i])[0]))
    if "param: Generator_Types" in Data_import[i]:      
        n_generators = int((re.findall('\d+',Data_import[i])[0]))

scenario = [i for i in range(1,n_scenarios+1)]
year = [i for i in range(1,n_years+1)]
period = [i for i in range(1,n_periods+1)]
generator = [i for i in range(1,n_generators+1)]

#%% This section is useful to define the number of investment steps as well as to assign each year to its corresponding step
def Initialize_Upgrades_Number(model):
    Data_file = "Inputs/data.dat"
    Data_import = open(Data_file).readlines()
    
    for i in range(len(Data_import)):
        if "param: Years" in Data_import[i]:
            n_years = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Step_Duration" in Data_import[i]:
            step_duration = int((re.findall('\d+',Data_import[i])[0]))
        if "param: Min_Last_Step_Duration" in Data_import[i]:
            min_last_step_duration = int((re.findall('\d+',Data_import[i])[0]))

    if n_years % step_duration == 0:
        n_upgrades = n_years/step_duration
        return n_upgrades
    
    else:
        n_upgrades = 1
        for y in  range(1, n_years + 1):
            if y % step_duration == 0 and n_years - y > min_last_step_duration:
                n_upgrades += 1
        return int(n_upgrades)

def Initialize_YearUpgrade_Tuples(model):
    upgrade_years_list = [1 for i in range(len(model.steps))]
    s_dur = model.Step_Duration   
    for i in range(1, len(model.steps)): 
        upgrade_years_list[i] = upgrade_years_list[i-1] + s_dur    
    yu_tuples_list = [0 for i in model.years]    
    if model.Steps_Number == 1:    
        for y in model.years:            
            yu_tuples_list[y-1] = (y, 1)    
    else:        
        for y in model.years:            
            for i in range(len(upgrade_years_list)-1):
                if y >= upgrade_years_list[i] and y < upgrade_years_list[i+1]:
                    yu_tuples_list[y-1] = (y, model.steps[i+1])                
                elif y >= upgrade_years_list[-1]:
                    yu_tuples_list[y-1] = (y, len(model.steps))   
    print('\nTime horizon (year,investment-step): ' + str(yu_tuples_list))
    return yu_tuples_list

#%% Time resolution adjusting process + creating the 20 years demand curve


data30 = pd.read_csv('C:/Users/pietr/Spyder/RAMP_spyder/results/output_file_1.csv', index_col=0)
data31 = pd.DataFrame(data30)
data31 = data31.append(data30[0:1440])
index30 = pd.date_range(start='2016-01-01 00:00:00',periods = len(data30), 
                                   freq=('1min'))
index31 = pd.date_range(start='2016-01-01 00:00:00',periods = len(data31), 
                                   freq=('1min'))




data30.index30 = index30
data31.index31 = index31

data30['day']  = data30.index30.dayofyear
data31['day']  = data31.index31.dayofyear
data30['hour'] = data30.index30.hour
data31['hour'] = data31.index31.hour
Demand_adjusted30 = data30.groupby(['day', 'hour']).mean()
Demand_adjusted31 = data31.groupby(['day', 'hour']).mean()

Demand_30 = pd.DataFrame()
Demand_31 = pd.DataFrame()

for i in range(1,7+1):

    Demand_30 = pd.concat([Demand_adjusted30,Demand_30], axis=0)
    
for i in range(1,5+1):
    Demand_31 = pd.concat([Demand_adjusted31,Demand_31], axis=0)


Demand = pd.DataFrame()
Demand = pd.concat([Demand_31, Demand_30], axis=0)

Demand_20years =pd.DataFrame()


for i in range(1,20+1):
    Demand_20years =pd.concat([Demand_20years, Demand],axis=1)

index = list(range(1,8760+1))
Demand_20years.index = index

years = list(range(1,20+1))
Demand_20years.columns = years
print(type(years))

Demand_20years.to_excel('C:/Users/pietr/Spyder/RAMP_spyder/results/Demand_20years.xlsx')

#Demand_final = pd.read_excel('C:/Users/pietr/Spyder/RAMP_spyder/results/Demand_20years.xlsx',index_col=0)


#%% This section imports the multi-year Demand and Renewable-Energy output and creates a Multi-indexed DataFrame for it
Demand = pd.read_excel('C:/Users/pietr/Spyder/RAMP_spyder/results/Demand_20years.xlsx',index_col=0)
Energy_Demand_Series = pd.Series()
for i in range(1,n_years*n_scenarios+1):
    dum = Demand[i][:]
    Energy_Demand_Series = pd.concat([Energy_Demand_Series,dum])
Energy_Demand = pd.DataFrame(Energy_Demand_Series) 
frame = [scenario,year,period]
index = pd.MultiIndex.from_product(frame, names=['scenario','year','period'])
Energy_Demand.index = index
Energy_Demand_2 = pd.DataFrame()    
for s in scenario:
    Energy_Demand_Series_2 = pd.Series()
    for y in year:
        dum_2 = Demand[(s-1)*n_years + y][:]
        Energy_Demand_Series_2 = pd.concat([Energy_Demand_Series_2,dum_2])
    Energy_Demand_2.loc[:,s] = Energy_Demand_Series_2
index_2 = pd.RangeIndex(1,n_years*n_periods+1)
Energy_Demand_2.index = index_2

def Initialize_Demand(model, s, y, t):
    return float(Energy_Demand[0][(s,y,t)])


#%% PV initializing
'''
import pandas as pd

ninja = pd.read_csv('C:/Users/pietr/Spyder/Micro_GRIDDDD.git/MicroGridsPy-SESAM-MYCE/Code/Inputs/ninja_pv.csv', header=None,index_col=0)# ricorda che qua ho dovuto eliminare manualmente le prime tre righe per farlo leggere come CSV

a = ninja.iloc[0:,1]*1000 #questa è la lista dei valori in Watt

df = pd.DataFrame(a)
columns = [1]
df.columns = columns
index = list(range(1,8761))
df.index = index


df.to_excel('C:/Users/pietr/Spyder/Micro_GRIDDDD.git/MicroGridsPy-SESAM-MYCE/Code/Inputs/PV.xlsx')
'''

#%% How to deal with different time zones
'''

fuso = 5

for i in range(1,fuso):
    df.loc[i, [1]] = df.loc[8755+i,[1]]
    df.loc[8755+i,[1]] = df.loc[i, [1]]
'''

     #Renewable_Energy = pd.read_excel('C:/Users/pietr/Spyder/Micro_GRIDDDD.git/MicroGridsPy-SESAM-MYCE/Code/Inputs/PV.xlsx',index_col=0)
Renewable_Energy = pd.read_excel('Inputs/PV.xlsx',index_col=0)
#columns_RES = [1,2]
#Renewable_Energy.columns = columns_RES   
#Renewable_Energy[1] = df[1]

     #Renewable_Energy['PV'] = df['PV']

def Initialize_RES_Energy(model,s,r,t):
    column = (s-1)*model.RES_Sources + r 
    
    return float(Renewable_Energy[column][t])   



  
def Initialize_Battery_Unit_Repl_Cost(model):
    Unitary_Battery_Cost = model.Battery_Specific_Investment_Cost - model.Battery_Specific_Electronic_Investment_Cost
    return Unitary_Battery_Cost/(model.Battery_Cycles*2*(1-model.Battery_Depth_of_Discharge))
    
    


def Initialize_Battery_Minimum_Capacity(model,ut):   
    Periods = model.Battery_Independence*24
    Len =  int(model.Periods*model.Years/Periods)
    Grouper = 1
    index = 1
    for i in range(1, Len+1):
        for j in range(1,Periods+1):      
            Energy_Demand_2.loc[index, 'Grouper'] = Grouper
            index += 1      
        Grouper += 1

    upgrade_years_list = [1 for i in range(len(model.steps))]
    
    for u in range(1, len(model.steps)):
        upgrade_years_list[u] =upgrade_years_list[u-1] + model.Step_Duration
    if model.Steps_Number ==1:
        Energy_Demand_Upgrade = Energy_Demand_2    
    else:
        if ut==1:
            start = 0
            Energy_Demand_Upgrade = Energy_Demand_2.loc[start : model.Periods*(upgrade_years_list[ut]-1), :]       
        elif ut == len(model.steps):
            start = model.Periods*(upgrade_years_list[ut-1] -1)+1
            Energy_Demand_Upgrade = Energy_Demand_2.loc[start :, :]       
        else:
            start = model.Periods*(upgrade_years_list[ut-1] -1)+1
            Energy_Demand_Upgrade = Energy_Demand_2.loc[start : model.Periods*(upgrade_years_list[ut]-1), :]
    
    Period_Energy = Energy_Demand_Upgrade.groupby(['Grouper']).sum()        
    Period_Average_Energy = Period_Energy.mean()
    Available_Energy = sum(Period_Average_Energy[s]*model.Scenario_Weight[s] for s in model.scenarios) 
    
    return  Available_Energy/(1-model.Battery_Depth_of_Discharge)

#%% This function calculates
def Initialize_Generator_Marginal_Cost(model,s,y,g):
    return model.Fuel_Specific_Cost[g]/(model.Fuel_LHV[g]*model.Generator_Efficiency[g])
