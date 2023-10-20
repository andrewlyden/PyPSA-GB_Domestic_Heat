import pandas as pd
import csv
from datetime import datetime
from meteostat import Point, Hourly

import sys

# one year data for the year,2022
start=datetime(2020,1,1)
end=datetime(2020,12,30,23, 59)


df_buses = pd.read_csv('data/buses_ZM.csv', index_col=0)

Z10=Point(df_buses.iloc[0].y,df_buses.iloc[0].x)
Z11=Point(df_buses.iloc[1].y,df_buses.iloc[1].x)
Z12=Point(df_buses.iloc[2].y,df_buses.iloc[2].x)
Z13=Point(df_buses.iloc[3].y,df_buses.iloc[3].x)
Z14=Point(df_buses.iloc[4].y,df_buses.iloc[4].x)
Z15= Point(df_buses.iloc[5].y,df_buses.iloc[5].x)
Z16=Point(df_buses.iloc[6].y,df_buses.iloc[6].x)  
Z17= Point(df_buses.iloc[7].y,df_buses.iloc[7].x)
Z1_1=Point(df_buses.iloc[8].y,df_buses.iloc[8].x)
Z1_2=Point(df_buses.iloc[9].y,df_buses.iloc[9].x)     
Z1_3=Point(df_buses.iloc[10].y,df_buses.iloc[10].x)  
Z1_4=Point(df_buses.iloc[11].y,df_buses.iloc[11].x) 
Z2=Point(df_buses.iloc[12].y,df_buses.iloc[12].x) 
#Z3=Point(df_buses.iloc[13].y,df_buses.iloc[13].x) 
#Z4=Point(df_buses.iloc[14].y,df_buses.iloc[14].x) 

Z3=Point(56.41390565703843, -3.4355159528296033)    # taking the perth station
Z4=Point(56.36313726304405, -5.036970295329588)


Z5=Point(df_buses.iloc[15].y,df_buses.iloc[15].x) 
Z6=Point(df_buses.iloc[16].y,df_buses.iloc[16].x) 
Z7=Point(df_buses.iloc[17].y,df_buses.iloc[17].x) 
Z8= Point(df_buses.iloc[18].y,df_buses.iloc[18].x) 
Z9= Point(df_buses.iloc[19].y,df_buses.iloc[19].x) 


# extract the outdoor air tempreature for the above nodes
weather_Z10=Hourly(Z10,start,end).fetch()['temp'].rename('Z10_tempreature')


weather_Z11=Hourly(Z11,start,end).fetch()['temp'].rename('Z11_tempreature')

# Since we coudn't get weather data close to errochty we searched another weather station in the council area Perth and Kinross,and extracted weather data for that particular location
#Errochty=Point(56.22,-3.30034)
weather_Z12=Hourly(Z12,start,end).fetch()['temp'].rename('Z12_tempreature')


weather_Z13=Hourly(Z13,start,end).fetch()['temp'].rename('Z13_tempreature')


weather_Z14=Hourly(Z14,start,end).fetch()['temp'].rename('Z14_tempreature')

weather_Z15=Hourly(Z15,start,end).fetch()['temp'].rename('Z15_tempreature')

weather_Z16=Hourly(Z16,start,end).fetch()['temp'].rename('Z16_tempreature')

#Strathaven=Point(55.80927,-4.35061)
weather_Z17=Hourly(Z17,start,end).fetch()['temp'].rename('Z17_tempreature')


# we presumed that there is no heat node around this station,the electric bus is the nuclear power station
weather_Z1_1=Hourly(Z1_1,start,end).fetch()['temp'].rename('Z1_1_tempreature') # nuclear power station, in East Lothian Council


weather_Z1_2=Hourly(Z1_2,start,end).fetch()['temp'].rename('Z1_2_tempreature')
weather_Z1_3=Hourly(Z1_3,start,end).fetch()['temp'].rename('Z1_3_tempreature')
weather_Z1_4=Hourly(Z1_4,start,end).fetch()['temp'].rename('Z1_4_tempreature')
weather_Z2=Hourly(Z2,start,end).fetch()['temp'].rename('Z2_tempreature')

weather_Z3=Hourly(Z3,start,end).fetch()['temp'].rename('Z3_tempreature')
weather_Z4=Hourly(Z4,start,end).fetch()['temp'].rename('Z4_tempreature')

weather_Z5=Hourly(Z5,start,end).fetch()['temp'].rename('Z5_tempreature')
weather_Z6=Hourly(Z6,start,end).fetch()['temp'].rename('Z6_tempreature')
weather_Z7=Hourly(Z7,start,end).fetch()['temp'].rename('Z7_tempreature')
weather_Z8=Hourly(Z8,start,end).fetch()['temp'].rename('Z8_tempreature')
weather_Z9=Hourly(Z9,start,end).fetch()['temp'].rename('Z9_tempreature')

#Hourly data
gbZones_temp=pd.concat([weather_Z10,weather_Z11,weather_Z12,weather_Z13,weather_Z14,weather_Z15,weather_Z16,weather_Z17,weather_Z1_1,weather_Z1_2,weather_Z1_3,weather_Z1_4,weather_Z2,weather_Z3,weather_Z4,weather_Z5,weather_Z6,weather_Z7,weather_Z8,weather_Z9],axis=1)
#scotlandNodes_temp.to_csv('data/scotlandNodes_temp.csv',header=True)




# fill the missing values if there are any
for column in gbZones_temp.columns:
    # Check if there are any missing values in the column
    if gbZones_temp[column].isnull().sum() > 0:
        # Find the index of the next column
        next_column_index = gbZones_temp.columns.get_loc(column) + 1
        # Fill missing values in the current column from the next column
        gbZones_temp[column].fillna(gbZones_temp.iloc[:, next_column_index], inplace=True)
        
        
gbZones_temp.to_csv('data/gbZones_temp.csv',index_label='time',header=True)