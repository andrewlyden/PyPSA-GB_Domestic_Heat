import pandas as pd
import csv
from datetime import datetime
from meteostat import Point, Hourly

import sys

# one year data for the year,2022
start=datetime(2022,1,1)
end=datetime(2022,12,31,23, 59)


df_buses = pd.read_csv('data/buses.csv', index_col=0)

Beauly=Point(df_buses.iloc[0].y,df_buses.iloc[0].x)
Peterhead=Point(df_buses.iloc[1].y,df_buses.iloc[1].x)
Errochty=Point(df_buses.iloc[2].y,df_buses.iloc[2].x)
Denny_Bonnybridge=Point(df_buses.iloc[3].y,df_buses.iloc[3].x)
Neilston=Point(df_buses.iloc[4].y,df_buses.iloc[4].x)
Strathaven= Point(df_buses.iloc[5].y,df_buses.iloc[5].x)

Torness=Point(df_buses.iloc[6].y,df_buses.iloc[6].x)    # nuclear power station, in East Lothian Council


Eccles= Point(df_buses.iloc[7].y,df_buses.iloc[7].x)
Harker=Point(df_buses.iloc[8].y,df_buses.iloc[8].x)
Stella_West=Point(df_buses.iloc[9].y,df_buses.iloc[9].x)     
Penwortham=Point(df_buses.iloc[10].y,df_buses.iloc[10].x)  
Deeside=Point(df_buses.iloc[11].y,df_buses.iloc[11].x) 
Daines=Point(df_buses.iloc[12].y,df_buses.iloc[12].x) 
Marsh_Stocksbridge=Point(df_buses.iloc[13].y,df_buses.iloc[13].x) 
Thornton_Drax_Eggborough=Point(df_buses.iloc[14].y,df_buses.iloc[14].x) 
Keadby=Point(df_buses.iloc[15].y,df_buses.iloc[15].x) 
Ratcliffe=Point(df_buses.iloc[16].y,df_buses.iloc[16].x) 
Feckenham=Point(df_buses.iloc[17].y,df_buses.iloc[17].x) 
Walpole= Point(df_buses.iloc[18].y,df_buses.iloc[18].x) 
Bramford= Point(df_buses.iloc[19].y,df_buses.iloc[19].x) 
Pelham= Point(df_buses.iloc[20].y,df_buses.iloc[20].x) 
Sundon_East_Claydon=Point(df_buses.iloc[21].y,df_buses.iloc[21].x) 
Melksham=Point(df_buses.iloc[22].y,df_buses.iloc[22].x) 
Bramley=Point(df_buses.iloc[23].y,df_buses.iloc[23].x) 
London=Point(df_buses.iloc[24].y,df_buses.iloc[24].x) 
Kemsley=Point(df_buses.iloc[25].y,df_buses.iloc[25].x) 
Sellindge= Point(df_buses.iloc[26].y,df_buses.iloc[26].x) 
Lovedean=Point(df_buses.iloc[27].y,df_buses.iloc[26].x) 
S_W_Penisula=Point(df_buses.iloc[28].y,df_buses.iloc[28].x) 

# extract the outdoor air tempreature for the above nodes
weather_beauly=Hourly(Beauly,start,end).fetch()['temp'].rename('beauly_tempreature')

#re-sample to half hourly
weather_beauly_halfhourly=weather_beauly.resample('30T').ffill()
weather_peterhead=Hourly(Peterhead,start,end).fetch()['temp'].rename('peterhead_tempreature')
#re-sample to half hourly
weather_peterhead_halfhourly=weather_peterhead.resample('30T').ffill()
# Since we coudn't get weather data close to errochty we searched another weather station in the council area Perth and Kinross,and extracted weather data for that particular location
Errochty=Point(56.22,-3.30034)
weather_errochty=Hourly(Errochty,start,end).fetch()['temp'].rename('errochty_tempreature')
#re-sample to half hourly
weather_errochty_halfhourly=weather_errochty.resample('30T').ffill()

weather_denny_bonnybridge=Hourly(Denny_Bonnybridge,start,end).fetch()['temp'].rename('denny_bonny_tempreature')
#re-sample to half hourly
weather_denny_bonnybridge_halfhourly=weather_denny_bonnybridge.resample('30T').ffill()

weather_neilston=Hourly(Neilston,start,end).fetch()['temp'].rename('neilston_tempreature')
#re-sample to half hourly
weather_neilston_halfhourly=weather_neilston.resample('30T').ffill()

Strathaven=Point(55.80927,-4.35061)
weather_strathaven=Hourly(Strathaven,start,end).fetch()['temp'].rename('strathaven_tempreature')
#re-sample to half hourly
weather_strathaven_halfhourly=weather_strathaven.resample('30T').ffill()

# we presumed that there is no heat node around this station,the electric bus is the nuclear power station
weather_torness=Hourly(Torness,start,end).fetch()['temp'].rename('torness_tempreature') # nuclear power station, in East Lothian Council
#re-sample to half hourly
weather_torness_halfhourly=weather_torness.resample('30T').ffill()

weather_eccles=Hourly(Eccles,start,end).fetch()['temp'].rename('eccles_tempreature')

#Hourly data
scotlandNodes_temp=pd.concat([weather_beauly,weather_errochty,weather_peterhead,weather_denny_bonnybridge,weather_neilston, weather_strathaven,weather_torness],axis=1)
#scotlandNodes_temp.to_csv('data/scotlandNodes_temp.csv',header=True)

# Halfhourly data

scotlandNodes_temp_halfhourly=pd.concat([weather_beauly_halfhourly,weather_errochty_halfhourly,weather_peterhead_halfhourly,weather_denny_bonnybridge_halfhourly,weather_neilston_halfhourly, weather_strathaven_halfhourly,weather_torness_halfhourly],axis=1)
#scotlandNodes_temp_halfhourly.to_csv('data/scotlandNodes_temp_halfhourly.csv',header=True)

# England Nodes
Eccles= Point(df_buses.iloc[7].y,df_buses.iloc[7].x)
Harker=Point(df_buses.iloc[8].y,df_buses.iloc[8].x)
Stella_West=Point(df_buses.iloc[9].y,df_buses.iloc[9].x)     
Penwortham=Point(df_buses.iloc[10].y,df_buses.iloc[10].x)  
Deeside=Point(df_buses.iloc[11].y,df_buses.iloc[11].x) 
Daines=Point(df_buses.iloc[12].y,df_buses.iloc[12].x) 

Marsh_Stocksbridge=Point(df_buses.iloc[13].y,df_buses.iloc[13].x) 

Thornton_Drax_Eggborough=Point(df_buses.iloc[14].y,df_buses.iloc[14].x) 
Keadby=Point(df_buses.iloc[15].y,df_buses.iloc[15].x) 
Ratcliffe=Point(df_buses.iloc[16].y,df_buses.iloc[16].x) 
Feckenham=Point(df_buses.iloc[17].y,df_buses.iloc[17].x) 
Walpole= Point(df_buses.iloc[18].y,df_buses.iloc[18].x) 
Bramford= Point(df_buses.iloc[19].y,df_buses.iloc[19].x) 
Pelham= Point(df_buses.iloc[20].y,df_buses.iloc[20].x) 
Sundon_East_Claydon=Point(df_buses.iloc[21].y,df_buses.iloc[21].x) 
Melksham=Point(df_buses.iloc[22].y,df_buses.iloc[22].x) 
Bramley=Point(df_buses.iloc[23].y,df_buses.iloc[23].x) 
London=Point(df_buses.iloc[24].y,df_buses.iloc[24].x) 
Kemsley=Point(df_buses.iloc[25].y,df_buses.iloc[25].x) 
Sellindge= Point(df_buses.iloc[26].y,df_buses.iloc[26].x) 

Lovedean=Point(df_buses.iloc[27].y,df_buses.iloc[26].x) 
S_W_Penisula=Point(df_buses.iloc[28].y,df_buses.iloc[28].x) 


# hourly tempreature data for england nodes in the PyPSA-GB model
weather_harker=Hourly(Harker,start,end).fetch()['temp'].rename('harker_tempreature')
weather_stella_west=Hourly(Stella_West,start,end).fetch()['temp'].rename('stella_west_tempreature')
weather_penwortham=Hourly(Penwortham,start,end).fetch()['temp'].rename('penwortham_tempreature')
weather_deeside=Hourly(Deeside,start,end).fetch()['temp'].rename('deeside_tempreature')
weather_daines=Hourly(Daines,start,end).fetch()['temp'].rename('daines_tempreature')


#Marsh_Stocksbridge=Point(53.39174,-1.47337)
Marsh_Stoksbridge=Point(53.95,-1.06)    # set the location information of the nearby area, York in this case
weather_marsh_stocksbridge=Hourly(Marsh_Stocksbridge,start,end).fetch()['temp'].rename('marsh_stocksbridge_tempreature')

weather_thornton_drax_eggborough=Hourly(Thornton_Drax_Eggborough,start,end).fetch()['temp'].rename('thornton_drax_eggborough_tempreature')
weather_keadby=Hourly(Keadby,start,end).fetch()['temp'].rename('keadby_tempreature')
weather_ratcliffe=Hourly(Ratcliffe,start,end).fetch()['temp'].rename('ratcliffe_tempreature')
weather_feckenham=Hourly(Feckenham,start,end).fetch()['temp'].rename('feckenham_tempreature')
weather_walpole=Hourly(Walpole,start,end).fetch()['temp'].rename('walpole_tempreature')
weather_bramford=Hourly(Bramford,start,end).fetch()['temp'].rename('bramford_tempreature')
weather_pelham=Hourly(Pelham,start,end).fetch()['temp'].rename('pelham_tempreature')
weather_sundon_east_claydon=Hourly(Sundon_East_Claydon,start,end).fetch()['temp'].rename('sundon_east_claydon_tempreature')
weather_melksham=Hourly(Melksham,start,end).fetch()['temp'].rename('melksham_tempreature')
weather_bramley=Hourly(Bramley,start,end).fetch()['temp'].rename('bramley_tempreature')
weather_london=Hourly(London,start,end).fetch()['temp'].rename('london_tempreature')
weather_kemsley=Hourly(Kemsley,start,end).fetch()['temp'].rename('kemsley_tempreature')
weather_sellindge=Hourly(Sellindge,start,end).fetch()['temp'].rename('sellindge_tempreature')
Lovedean=Point(50.91672,-1.03955)
weather_lovedean=Hourly(Lovedean,start,end).fetch()['temp'].rename('lovedean_tempreature')
weather_s_w_penisula=Hourly(S_W_Penisula,start,end).fetch()['temp'].rename('s_w_penisula_tempreature')


# Hourly tempreature data for England nodes
englandNodes_temp=pd.concat([weather_eccles,weather_harker,weather_stella_west,weather_penwortham,weather_deeside, weather_daines,weather_marsh_stocksbridge, weather_thornton_drax_eggborough, weather_keadby, weather_ratcliffe, weather_feckenham, weather_walpole, weather_bramford, weather_pelham, weather_sundon_east_claydon, weather_melksham, weather_bramley, weather_london, weather_kemsley, weather_sellindge,weather_lovedean, weather_s_w_penisula],axis=1)




# Hourly tempreature data for all nodes in the PyPSA-GB

gbNodes_temp=pd.concat([weather_beauly,weather_errochty,weather_peterhead,weather_denny_bonnybridge,weather_neilston,weather_strathaven,weather_torness,weather_eccles,weather_harker,weather_stella_west,weather_penwortham,weather_deeside, weather_daines,weather_marsh_stocksbridge, weather_thornton_drax_eggborough, weather_keadby, weather_ratcliffe, weather_feckenham, weather_walpole, weather_bramford, weather_pelham, weather_sundon_east_claydon, weather_melksham, weather_bramley, weather_london, weather_kemsley, weather_sellindge,weather_lovedean, weather_s_w_penisula],axis=1)



# fill the missing values if there are any
for column in gbNodes_temp.columns:
    # Check if there are any missing values in the column
    if gbNodes_temp[column].isnull().sum() > 0:
        # Find the index of the next column
        next_column_index = gbNodes_temp.columns.get_loc(column) + 1
        # Fill missing values in the current column from the next column
        gbNodes_temp[column].fillna(gbNodes_temp.iloc[:, next_column_index], inplace=True)
        
        
gbNodes_temp.to_csv('data/gbNodes_temp.csv',index_label='time',header=True)