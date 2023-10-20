import csv
import pandas as pd
from datetime import datetime

# Estimating the daily heat demand and the coefficient of performance for heat pumps from the daily temperature profile using the regression equations derived by Watson. et al. The regression equations are derived from trained data with a limited temperature range, however, these equations are applied for all temperature ranges above and below the breakpoint temperature, therefore, the heat demand estimation might lead to a very high estimate as opposed to the actual heat demand.

# Let us do the implementation from the EDRP dataset, THIS IS FOR GAS BOILERS

# See Table 1, https://www.sciencedirect.com/science/article/pii/S037877882100061X
m_total_1=-5.463
b_total_1=90.55

breakpoint_temp_EDRP=14.2

m_total_2=-0.988
b_total_2=26.84


# Read the temperature data for all nodes in the PyPSA-GB
modell='zonal'
##model='reduced'
if modell=='zonal':
    outdoor_temp=pd.read_csv('data/gbZones_temp.csv')
    outdoor_temp['time'] = pd.to_datetime(outdoor_temp['time']).dt.strftime('%d/%m/%Y %H:%M:%S')
else:
    outdoor_temp=pd.read_csv('data/gbNodes_temp.csv')
timestamps=outdoor_temp.time.values.tolist()

# let us assume the same outdoor temperature for the FES as well, only change the time stamps
def update_year_in_Timestamp(timestamps, fes_year):
    updated_timestamps = []
    for timestamp in timestamps:
        # Split the timestamp into date and time parts
        date_part, time_part = timestamp.split(' ')
        # Split the date part into day, month, and year
        day, month, year = date_part.split('/')
        # Update the year with the new_year value
        year = fes_year
        # Reassemble the date part and time part to form the updated timestamp
        updated_timestamp = f'{day}/{month}/{year} {time_part}'
        updated_timestamps.append(updated_timestamp)
        Timestamp=updated_timestamps
    return Timestamp




def hourly_heat_temp_EDRP(heat_node,ndgs,fes_year):
    for heat_node_name in heat_node:
        if fes_year=='2035':
            filename='data/domestic_EDRP/2035/hourly heat demand total_' + heat_node_name + '.csv'
            temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        elif fes_year=='2050':
            filename='data/domestic_EDRP/2050/hourly heat demand total_' + heat_node_name + '.csv'
            temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        #Timestamp=outdoor_temp.time.values.tolist()
        Timestamp=update_year_in_Timestamp(timestamps, fes_year)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Ambient Temp', 'Heat Demand'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp < breakpoint_temp_EDRP:
                    hourly_heat_demand_total = m_total_1 * temp + b_total_1
                    hourly_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*hourly_heat_demand_total
                    writer.writerow([stamp,temp, hourly_heat_demand_total])
                 
                else:
                    if temp>26.5:       #   setting this value much lower could give better estimation, example after temp>18 set the temp 18
                        temp=26.5        #
                        hourly_heat_demand_total = m_total_2 * temp + b_total_2
                        hourly_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*hourly_heat_demand_total
                        writer.writerow([stamp,temp, hourly_heat_demand_total])
                    else:    
                        hourly_heat_demand_total = m_total_2 * temp + b_total_2
                        hourly_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*hourly_heat_demand_total
                        writer.writerow([stamp,temp, hourly_heat_demand_total])
    
        if fes_year=='2035':
            df_buses_total=pd.read_csv('data/domestic_EDRP/2035/hourly heat demand total_' + heat_node_name + '.csv', index_col=0)
            filename_peak='data/domestic_EDRP/2035/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
         
        elif fes_year=='2050':
            df_buses_total=pd.read_csv('data/domestic_EDRP/2050/hourly heat demand total_' + heat_node_name + '.csv', index_col=0)
            filename_peak='data/domestic_EDRP/2050/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'  
        with open(filename_peak,'w',newline='') as csvfile:
            writer =csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand'])
            for i in range(0,len(df_buses_total['Heat Demand']), 24):
                daily_total=sum(df_buses_total['Heat Demand'][i:i+24])
                for timestamp_hourly,half in zip(Timestamp[i:i+24],range(i,i+24)):
                    writer.writerow([timestamp_hourly,daily_total])
                    
                    
                    
                    #next we have to modify the daily heat demand with the normalised profiles
        Normalised_profile=pd.read_csv('data/domestic_EDRP/scaled with normalised profiles/Normalised Total profile_EDRP.csv')
        hourly_nd = Normalised_profile.groupby(Normalised_profile.index // 2).mean(numeric_only=True)            
        if fes_year=='2035':
            filename_withnorm='data/domestic_EDRP/2035/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
            daily_total=pd.read_csv('data/domestic_EDRP/2035/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
        elif fes_year=='2050':
            filename_withnorm='data/domestic_EDRP/2050/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
            daily_total=pd.read_csv('data/domestic_EDRP/2050/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
            
        
        with open(filename_withnorm,'w',newline='') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand With Gas Boilers'])
            n_days=365
            for hour,temp in zip(Timestamp,temp_list):
                if temp<-1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 1'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=-1.5 and temp<1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 2'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=1.5 and temp<4.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 3'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=4.5 and temp<7.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 4'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=7.5 and temp<10.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 5'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=10.5 and temp<13.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 6'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=13.5 and temp<16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 7'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif temp>16.5 and temp<19.5:
                elif temp>=16.5:    # Watson did't consider space heating above 19.5, consider
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 8'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif:
                   # There is missing data in the Peterhead temperature around 4k, check that again or fill in the missing value
              
            
            # Heat demand profile generation with DHN, REGRESSION EQUATIONS DERIVED FROM GAS BOILER DATA ARE USED IN THIS CASE
                    
def hourly_heat_temp_EDRP_DHN(heat_node,ndgs,fes_year):
    for heat_node_name in heat_node:
        if fes_year=='2035':
            filename='data/domestic_EDRP_DHN/2035/hourly heat demand total_' + heat_node_name + '.csv'
            temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        elif fes_year=='2050':
            filename='data/domestic_EDRP_DHN/2050/hourly heat demand total_' + heat_node_name + '.csv'
            temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
            
            
        

        Timestamp=update_year_in_Timestamp(timestamps, fes_year)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Ambient Temp', 'Heat Demand'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp < breakpoint_temp_EDRP:
                    hourly_heat_demand_total = m_total_1 * temp + b_total_1
                    hourly_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*hourly_heat_demand_total
                    writer.writerow([stamp,temp, hourly_heat_demand_total])
                 
                else:
                    hourly_heat_demand_total = m_total_2 * temp + b_total_2
                    hourly_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*hourly_heat_demand_total
                    writer.writerow([stamp,temp, hourly_heat_demand_total])
    
        if fes_year=='2035':
            df_buses_total=pd.read_csv('data/domestic_EDRP_DHN/2035/hourly heat demand total_' +heat_node_name + '.csv',index_col=0)
            filename_peak='data/domestic_EDRP_DHN/2035/daily_demand/daily heat demand total_' +heat_node_name + '.csv'
        elif fes_year=='2050':
            df_buses_total=pd.read_csv('data/domestic_EDRP_DHN/2050/hourly heat demand total_' +heat_node_name + '.csv',index_col=0)
            filename_peak='data/domestic_EDRP_DHN/2050/daily_demand/daily heat demand total_' +heat_node_name + '.csv'
        with open(filename_peak,'w',newline='') as csvfile:
            writer =csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand'])
            for i in range(0,len(df_buses_total['Heat Demand']), 24):
                daily_total=sum(df_buses_total['Heat Demand'][i:i+24])
                for timestamp_hourly,half in zip(Timestamp[i:i+24],range(i,i+24)):
                    writer.writerow([timestamp_hourly,daily_total])
                    
                    
                    #next we have to modify the daily heat demand with the normalised profiles
        Normalised_profile=pd.read_csv('data/domestic_EDRP_DHN/scaled with normalised profiles/Normalised Total profile_EDRP.csv')
        hourly_nd = Normalised_profile.groupby(Normalised_profile.index // 2).mean(numeric_only=True) 
        
        
        if fes_year=='2035':
            filename_withnorm='data/domestic_EDRP_DHN/2035/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
            daily_total=pd.read_csv('data/domestic_EDRP_DHN/daily_demand/daily heat demand total_' + heat_node_name + '.csv')
        elif fes_year=='2050':
            filename_withnorm='data/domestic_EDRP_DHN/2050/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
            daily_total=pd.read_csv('data/domestic_EDRP_DHN/2050/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
 
       
        with open(filename_withnorm,'w',newline='') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand With Gas Boilers'])
            n_days=365
            for hour,temp in zip(Timestamp,temp_list):
                if temp<-1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 1'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=-1.5 and temp<1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 2'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=1.5 and temp<4.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 3'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=4.5 and temp<7.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 4'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=7.5 and temp<10.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 5'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=10.5 and temp<13.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 6'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=13.5 and temp<16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 7'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif temp>16.5 and temp<19.5:
                elif temp>=16.5:    # Watson did't consider space heating above 19.5, consider
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 8'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['Heat Demand'][idx]
                    writer.writerow([hour,heat_demand]) 


 # Doing the same implementation using the RHPP equations, HPS

# See Table 1,https://www.sciencedirect.com/science/article/pii/S037877882100061X

 # The combination of the heat pump installation is assumed as 75% ASHP and 25% GSHP
m_rhpp_1=-5.88
b_rhpp_1=97.2

breakpoint_temp_rhpp=14.3

m_rhpp_2=-1.11
b_rhpp_2=30


# Let us consider the same heating pattern will be followed irrespective of temperature,  THIS APPLIES REGRESSION EQUATIONS WITH HEAT PUMPS

def hourly_heat_temp_RHPP(heat_node,ndgs,fes_year,m):
    for heat_node_name in heat_node:
        if fes_year=='2035':
            if modell=='zonal':
                filename='data/domestic_RHPP/2035/ZonalModel/daily heat demand total_' + heat_node_name + '.csv'
                temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
            else: # reduced model
                filename='data/domestic_RHPP/2035/daily heat demand total_' + heat_node_name + '.csv'
                temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        elif fes_year=='2050': # this is not implemented for the zonal model at the moment
            filename='data/domestic_RHPP/2050/daily heat demand total_' + heat_node_name + '.csv'
            temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
       
        Timestamp=update_year_in_Timestamp(timestamps, fes_year)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'HP total Demand'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp < breakpoint_temp_rhpp:
                    daily_heat_demand_total = m_rhpp_1 * temp + b_rhpp_1
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                 
                else:
                    daily_heat_demand_total = m_rhpp_2 * temp + b_rhpp_2
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                    #if temp>20:  will be preferable
                        #temp=20
                        #daily_heat_demand_total = m_rhpp_2 * temp + b_rhpp_2
                        #daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                writer.writerow([stamp,temp, daily_heat_demand_total])

        if fes_year=='2035':
            if modell=='zonal':
                df_buses_total=pd.read_csv('data/domestic_RHPP/2035/ZonalModel/daily heat demand total_' + heat_node_name + '.csv', index_col=0)
                filename_peak='data/domestic_RHPP/2035/ZonalModel/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
            else:
                df_buses_total=pd.read_csv('data/domestic_RHPP/2035/daily heat demand total_' + heat_node_name + '.csv', index_col=0)
                filename_peak='data/domestic_RHPP/2035/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
        elif fes_year=='2050':
            df_buses_total=pd.read_csv('data/domestic_RHPP/2050/daily heat demand total_' + heat_node_name + '.csv', index_col=0)
            filename_peak='data/domestic_RHPP/2050/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
        
        with open(filename_peak,'w',newline='') as csvfile:
            writer =csv.writer(csvfile)
            writer.writerow(['Timestamp','HP total Demand'])
            for i in range(0,len(df_buses_total['HP total Demand']), 24):
                daily_total=sum(df_buses_total['HP total Demand'][i:i+24])
                for timestamp_hourly,half in zip(Timestamp[i:i+24],range(i,i+24)):
                    writer.writerow([timestamp_hourly,daily_total])
        Normalised_profile=pd.read_csv('data/domestic_RHPP/scaled with normalised profiles/Normalised Total profile_RHPP.csv')
        hourly_nd = Normalised_profile.groupby(Normalised_profile.index // 2).mean(numeric_only=True)
        if fes_year=='2035':
            if modell=='zonal':
                filename_withnorm='data/domestic_RHPP/2035/ZonalModel/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
                daily_total=pd.read_csv('data/domestic_RHPP/2035/ZonalModel/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
            else: # reduced model
                filename_withnorm='data/domestic_RHPP/2035/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
                daily_total=pd.read_csv('data/domestic_RHPP/2035/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
        elif fes_year=='2050':
            filename_withnorm='data/domestic_RHPP/2050/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
            daily_total=pd.read_csv('data/domestic_RHPP/2050/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
        
        with open(filename_withnorm,'w',newline='') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand With HPs'])
            n_days=365
            for hour,temp in zip(Timestamp,temp_list):
                if temp<-1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 1'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=-1.5 and temp<1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 2'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=1.5 and temp<4.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 3'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=4.5 and temp<7.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 4'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=7.5 and temp<10.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 5'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=10.5 and temp<13.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 6'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=13.5 and temp<16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 7'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif temp>16.5 and temp<19.5:
                elif temp>=16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 8'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                        
         

        ##############################Let us disaggregate the heating demand to Airsource heat pumps and ground source heat pumps



def hourly_heat_temp_RHPP_ASHP(heat_node,ndgs):
    for heat_node_name in heat_node:
        filename='data/domestic_RHPP/ASHP/daily heat demand total_' + heat_node_name + '.csv'
        temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        Timestamp=update_year_in_Timestamp(Timestamp, fes_year)
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'HP total Demand'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp < breakpoint_temp_rhpp:
                    daily_heat_demand_total = m_rhpp_1 * temp + b_rhpp_1
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                 
                else:
                    daily_heat_demand_total = m_rhpp_2 * temp + b_rhpp_2
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                writer.writerow([stamp,temp, daily_heat_demand_total])

        
        df_buses_total=pd.read_csv('data/domestic_RHPP/ASHP/daily heat demand total_' + heat_node_name + '.csv', index_col=0)
        
        #filename_peak='./PyPSA-GB/Heat_demand_clustered_LAs/domestic_RHPP/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
        filename_peak='data/domestic_RHPP/ASHP/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
        with open(filename_peak,'w',newline='') as csvfile:
            writer =csv.writer(csvfile)
            writer.writerow(['Timestamp','HP total Demand'])
            for i in range(0,len(df_buses_total['HP total Demand']), 24):
                daily_total=sum(df_buses_total['HP total Demand'][i:i+24])
                for timestamp_hourly,half in zip(Timestamp[i:i+24],range(i,i+24)):
                    writer.writerow([timestamp_hourly,daily_total])
             
       # next we have to modify the daily gas demand with the normalised profiles
        
        Normalised_profile=pd.read_csv('data/domestic_RHPP/ASHP/scaled with normalised profiles/Normalised Total profile_RHPP.csv')
        hourly_nd = Normalised_profile.groupby(Normalised_profile.index // 2).mean(numeric_only=True)
    
        
        filename_withnorm='data/domestic_RHPP/ASHP/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
        
      
        daily_total=pd.read_csv('data/domestic_RHPP/ASHP/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
        with open(filename_withnorm,'w',newline='') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand With HPs'])
            n_days=365
            for hour,temp in zip(Timestamp,temp_list):
                if temp<-1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 1'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    #writer.writerow([Timestamp[idx],gas_demand])
                    writer.writerow([hour,heat_demand])
                elif temp>=-1.5 and temp<1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 2'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=1.5 and temp<4.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 3'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=4.5 and temp<7.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 4'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=7.5 and temp<10.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 5'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=10.5 and temp<13.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 6'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=13.5 and temp<16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 7'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif temp>16.5 and temp<19.5:
                elif temp>=16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 8'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                        
                             
                    
                    
                   #################GSHP
def hourly_heat_temp_RHPP_GSHP(heat_node,ndgs):
    for heat_node_name in heat_node:
        filename='data/domestic_RHPP/GSHP/daily heat demand total_' + heat_node_name + '.csv'
        temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        Timestamp=outdoor_temp.time.values.tolist()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'HP total Demand'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp < breakpoint_temp_rhpp:
                    daily_heat_demand_total = m_rhpp_1 * temp + b_rhpp_1
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                 
                else:
                    daily_heat_demand_total = m_rhpp_2 * temp + b_rhpp_2
                    daily_heat_demand_total=ndgs[heat_node.index(heat_node_name)]*daily_heat_demand_total
                writer.writerow([stamp,temp, daily_heat_demand_total])

        
        df_buses_total=pd.read_csv('data/domestic_RHPP/GSHP/daily heat demand total_' + heat_node_name + '.csv', index_col=0)
       
        filename_peak='data/domestic_RHPP/GSHP/daily_demand/daily heat demand total_'+ heat_node_name + '.csv'
        with open(filename_peak,'w',newline='') as csvfile:
            writer =csv.writer(csvfile)
            writer.writerow(['Timestamp','HP total Demand'])
            for i in range(0,len(df_buses_total['HP total Demand']), 24):
                daily_total=sum(df_buses_total['HP total Demand'][i:i+24])
                for timestamp_hourly,half in zip(Timestamp[i:i+24],range(i,i+24)):
                    writer.writerow([timestamp_hourly,daily_total])
             
       # next we have to modify the daily gas demand with the normalised profiles
        
        Normalised_profile=pd.read_csv('data/domestic_RHPP/GSHP/scaled with normalised profiles/Normalised Total profile_RHPP.csv')
        hourly_nd = Normalised_profile.groupby(Normalised_profile.index // 2).mean(numeric_only=True)
    
        filename_withnorm='data/domestic_RHPP/GSHP/scaled with normalised profiles/hourly heat demand total_' + heat_node_name + '.csv'
        
        daily_total=pd.read_csv('data/domestic_RHPP/GSHP/daily_demand/daily heat demand total_'+ heat_node_name + '.csv')
        with open(filename_withnorm,'w',newline='') as csvfile:
            writer=csv.writer(csvfile)
            writer.writerow(['Timestamp','Heat Demand With HPs'])
            n_days=365
            for hour,temp in zip(Timestamp,temp_list):
                if temp<-1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 1'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    #writer.writerow([Timestamp[idx],gas_demand])
                    writer.writerow([hour,heat_demand])
                elif temp>=-1.5 and temp<1.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 2'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=1.5 and temp<4.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 3'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=4.5 and temp<7.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 4'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=7.5 and temp<10.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 5'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=10.5 and temp<13.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 6'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                elif temp>=13.5 and temp<16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 7'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
                #elif temp>16.5 and temp<19.5:
                elif temp>=16.5:
                    idx=temp_list.index(temp)
                    Normalised_profile=hourly_nd['band 8'].values.tolist()*n_days
                    npf=Normalised_profile[idx]
                    heat_demand=npf*daily_total['HP total Demand'][idx]
                    writer.writerow([hour,heat_demand])
    # the efficiency of heat pump is also tempreature dependant and the hourly cop for the clustered nodes can be estimated below
   # Determine the COP for the combination of the heat pump installation is assumed as 75% ASHP and 25% GSHP
m_1=0.045
b_1=2.17

breakpoint_temp=7.7

m_2=-0.075
b_2=3.09   

def hourly_cop_temp(heat_node):
    for heat_node_name in heat_node:
        filename='data/domestic_RHPP/COP/hourly COP_' + heat_node_name + '.csv'
        temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        Timestamp=outdoor_temp.time.values.tolist()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'COP'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp<-5:
                    hourly_cop=1.8
                elif temp < breakpoint_temp_rhpp and temp>=-5:
                    hourly_cop = m_1 * temp + b_1
                    
                elif temp>breakpoint_temp_rhpp and temp<20:
                    hourly_cop = m_2 * temp + b_2
                elif temp>20:         # the data driven model considers upto this tempreature range
                    hourly_cop=1.4
                writer.writerow([stamp,temp, hourly_cop])

 
   
# write the csv file from here rather than manually creat the COP CSV file
########  Determine the CoP for the heat pump types separetely

######### ASHP
m_1=0.060
b_1=2.07

breakpoint_temp=8.2

m_2=-0.088
b_2=3.29  

def hourly_cop_temp_ASHP(heat_node):
    for heat_node_name in heat_node:
        filename='data/domestic_RHPP/COP/ASHP/hourly COP_' + heat_node_name + '.csv'
        temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        Timestamp=outdoor_temp.time.values.tolist()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'COP'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp<-5:
                    hourly_cop=1.8
                elif temp < breakpoint_temp_rhpp and temp>=-5:
                    hourly_cop = m_1 * temp + b_1
                    
                elif temp>breakpoint_temp_rhpp and temp<20:
                    hourly_cop = m_2 * temp + b_2
                elif temp>20:     #  The data-driven model considers up to this temperature range
                    hourly_cop=1.4
                writer.writerow([stamp,temp, hourly_cop])
                
        ##### GSHP     
m_1=0
b_1=2.50

breakpoint_temp=5

m_2=-0.053
b_2=2.77 
        
def hourly_cop_temp_GSHP(heat_node):
    for heat_node_name in heat_node:
        filename='data/domestic_RHPP/COP/GSHP/hourly COP_' + heat_node_name + '.csv'
        temp_list=outdoor_temp[heat_node_name+'_tempreature'].values.tolist()
        
        Timestamp=outdoor_temp.time.values.tolist()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp','Ambient Temp', 'COP'])
            for stamp,temp in zip(Timestamp,temp_list):
                if temp<-5:
                    hourly_cop=2.5
                elif temp < breakpoint_temp_rhpp and temp>=-5:
                    hourly_cop = m_1 * temp + b_1
                    
                elif temp>breakpoint_temp_rhpp and temp<20:
                    hourly_cop = m_2 * temp + b_2
                elif temp>20:     #  the data driven model cosiders upto this tempreature range
                    hourly_cop=1.7
                writer.writerow([stamp,temp, hourly_cop])               
                
