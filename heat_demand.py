import pandas as pd
import numpy as np
import calendar

import FES_heat_supply_data

import os
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import seaborn as sns
import geopandas as gpd


import cartopy.crs as ccrs
from cartopy.crs import PlateCarree as plate
import cartopy.io.shapereader as shpreader

import xarray as xr
import atlite

import logging
import warnings

import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

warnings.simplefilter('ignore')
logging.captureWarnings(False)
logging.basicConfig(level=logging.INFO)


def heat_demand_for_LA_half_hourly(LA, air_temp_daily, weather_year, future_year, FES, scenario, FES_scaling, normalised_profiles, LA_heat_pattern_total):

    # see https://doi.org/10.1016/j.enbuild.2021.110777

    try:
        df = pd.read_csv('data/heat_demand_profiles/' + LA + '_' + scenario + '_' + FES + '_' + str(weather_year) + '_' + str(future_year) + '.csv', index_col=0)

    except:
        HD_daily = heat_demand_for_LA_daily(LA, air_temp_daily, future_year, FES_scaling, LA_heat_pattern_total)
        # read in daily temps
        air_temp_daily = air_temp_daily[LA]
        # read the half hourly normalised profiles
        normalised_profile_daytime = normalised_profiles['daytime']
        normalised_profile_bimodal = normalised_profiles['bi-modal']
        normalised_profile_continuous = normalised_profiles['continuous']
        # check number of days in year
        daysinyear = 365 #+ calendar.isleap(future_year)
        # daysinyear = 2

        HD_half_hourly = {}
        for day in range(0, daysinyear):
            HD_tech_half_hourly = {}    
            for tech in HD_daily.index:
                day_string = str(future_year) + '-' + str(day)
                HD_tech_half_hourly[tech] = (HD_daily.loc[tech, day_string]['daytime'] *
                                            half_hourly_normalised_profiles(normalised_profile_daytime, air_temp_daily[day]) +
                                            HD_daily.loc[tech, day_string]['bi-modal'] *
                                            half_hourly_normalised_profiles(normalised_profile_bimodal, air_temp_daily[day]) +
                                            HD_daily.loc[tech, day_string]['continuous'] *
                                            half_hourly_normalised_profiles(normalised_profile_continuous, air_temp_daily[day]))
                HD_tech_half_hourly[tech].name = tech
                # print(day, tech)
            HD_half_hourly[day] = HD_tech_half_hourly

        df_list = []
        for day in range(0, daysinyear):
            reformed_dict = {}
            for outerKey, innerDict in HD_half_hourly.items():
                for innerKey, values in innerDict.items():
                    reformed_dict[(outerKey,
                                innerKey)] = values
            df = pd.DataFrame.from_dict(reformed_dict)[day]
            df_list.append(df)
        
        # random non-leap year used. but year is modified later.
        start = str(2021) + '-01-01'
        end = str(2021) + '-12-31 23:30:00'
        datetime_index = pd.date_range(start=start, end=end, freq='0.5H')
        df = pd.concat(df_list)
        df.index = datetime_index
        df.index = df.index + pd.DateOffset(year=future_year)
        df.to_csv('outputs/heat_demand_profiles/' + LA + '_' + scenario + '_' + FES + '_' + str(weather_year) + '_' + str(future_year) + '.csv')

    return df


def heat_demand_for_all_variables_LA_half_hourly(weather_year, future_year, FES, scenario):

    air_temp_daily = pd.read_csv('data/LA_UK/air_temp/average_day_air_temp_' + str(weather_year) + '.csv')
    normalised_profiles = {'daytime': pd.read_excel('data/normalised_half_hourly_profiles.xlsx', sheet_name='Total heat daytime HPs', usecols="B:I"),
                           'bi-modal': pd.read_excel('data/normalised_half_hourly_profiles.xlsx', sheet_name='Total heat bimodal HPs', usecols="B:I"),
                           'continuous': pd.read_excel('data/normalised_half_hourly_profiles.xlsx', sheet_name='Total heat continuous HPs', usecols="B:I")}
    LA_heat_pattern_total = LA_heat_pattern_totals(LA, future_year, FES, scenario)
    # get a list of LA
    # year dosent matter only used for getting LA list
    df = pd.read_csv('data/LA_UK/air_temp/air_temp_' + str(2015) + '.csv', index_col=0)
    LA_list = df.columns
    
    for LA in LA_list:
        print(LA, weather_year, future_year, FES, scenario)
        heat_demand_for_LA_half_hourly(LA, air_temp_daily, weather_year, future_year, FES, scenario, normalised_profiles, LA_heat_pattern_total[LA])


def heat_demand_for_LA_daily(LA, air_temp_daily, future_year, FES_scaling, LA_heat_pattern_total):

    # read in daily temps
    air_temp_daily = air_temp_daily[LA]
    # check number of days in year
    daysinyear = 365 #+ calendar.isleap(future_year)

    # scaling factor

    data = {}
    for day in range(0, daysinyear):
    # for day in range(1, 4):
        date_time = str(future_year) + '-' + str(day)
        Td = air_temp_daily.loc[day]
        data[date_time] = heat_demand_for_LA_for_one_day(
            LA_heat_pattern_total[LA], Td, FES_scaling)
        # print(data[date_time])
    reformed_dict = {}
    for outerKey, innerDict in data.items():
        for innerKey, values in innerDict.items():
            reformed_dict[(outerKey,
                        innerKey)] = values
    df = pd.DataFrame.from_dict(reformed_dict)

    return df

def heat_demand_for_LA_for_one_day(LA_heat_pattern_total, Td, FES_scaling):

    total_dwellings = LA_heat_pattern_total
    daytime = total_dwellings['daytime']
    bimodal = total_dwellings['bi-modal']
    continuous = total_dwellings['continuous']

    HD_tech = {'daytime': heat_demand_for_one_pattern_for_one_day(daytime, 'daytime', Td) * FES_scaling,
               'bi-modal': heat_demand_for_one_pattern_for_one_day(bimodal, 'bi-modal', Td) * FES_scaling,
               'continuous': heat_demand_for_one_pattern_for_one_day(continuous, 'continuous', Td) * FES_scaling}

    return HD_tech

def FES_scaling_factor_calc(future_year, FES, scenario):
    """
    Calculate the scaling factor for the heat demand data for a given year, FES year, and FES scenario.
    Needed due to large assumptions around fabric upgrades, building standards, and behavioural change in FES
    which drives down heat demand dramatically.
    """

    file = 'data/FES Spatial Heat Model/' + FES + '/' + 'Annual Heat Demand - FES' + FES[-2:] + '.csv'
    if scenario == 'LW':
        scenario = 'Leading the Way'
    elif scenario == 'CT':
        scenario = 'Consumer Transformation'
    elif scenario == 'ST':
        scenario = 'System Transformation'
    elif scenario == 'FS':
        scenario = 'Falling Short'
    elif scenario == 'SP':
        scenario = 'Steady Progression'
    data = pd.read_csv(file, index_col=0)
    future_heat_demand = data.loc[scenario, str(future_year)]
    # RHPP dataset is from 2014-2016 so using 2015 demand levels to scale against
    # However, the modelling predicts historic heat demand in 2020 exactly. So going with that as baseline fabric level.
    RHPP_heat_demand = data.loc['History', '2020']

    return future_heat_demand / RHPP_heat_demand


def half_hourly_normalised_profiles(heat_pattern_data, Td):

    normalised_profile = heat_pattern_data
    if Td < -4.5:
        normalised_profile = normalised_profile.iloc[:,0]
        # raise ValueError(f"Only day temperatures above -4.5 degrees are accepted: {Td}")
    elif Td >= -4.5 and Td < -1.5:
        normalised_profile = normalised_profile.iloc[:,0]
    elif Td >= -1.5 and Td < 1.5:
        normalised_profile = normalised_profile.iloc[:,1]
    elif Td >= 1.5 and Td < 4.5:
        normalised_profile = normalised_profile.iloc[:,2]
    elif Td >= 4.5 and Td < 7.5:
        normalised_profile = normalised_profile.iloc[:,3]
    elif Td >= 7.5 and Td < 10.5:
        normalised_profile = normalised_profile.iloc[:,4]
    elif Td >= 10.5 and Td < 13.5:
        normalised_profile = normalised_profile.iloc[:,5]
    elif Td >= 13.5 and Td < 16.5:
        normalised_profile = normalised_profile.iloc[:,6]
    elif Td >= 16.5:
        normalised_profile = normalised_profile.iloc[:,7]
    
    return normalised_profile

def heat_demand_for_one_pattern_for_one_day(total_dwellings_pattern, heating_pattern, Td):
    """
    Calculate the heat demand for one day for a given number of dwellings, heating pattern, and average day temperature.
    """
    if heating_pattern == 'daytime':
        C = {'TBp':14.3, 'mp1':-5.39, 'cp1':88.8, 'mp2':-0.94, 'cp2':25.0, 'R2':0.97}
    elif heating_pattern == 'bi-modal':
        C = {'TBp':13.9, 'mp1':-5.22, 'cp1':83.7, 'mp2':-0.82, 'cp2':22.4, 'R2':0.97}
    elif heating_pattern == 'continuous':
        C = {'TBp':14.3, 'mp1':-6.18, 'cp1':102.6, 'mp2':-1.24, 'cp2':31.8, 'R2':0.98}
    elif heating_pattern == 'ASHP':
        C = {'TBp':14.3, 'mp1':-5.85, 'cp1':96.7, 'mp2':-1.1, 'cp2':28.7}
    elif heating_pattern == 'GSHP':
        C = {'TBp':14.3, 'mp1':-5.96, 'cp1':98.7, 'mp2':-1.15, 'cp2':29.8}

    # given a number of buildings using a heating pattern, calculate the heat demand using coefficients
    if Td < C['TBp']:
        HD = C['mp1'] * Td + C['cp1']
    elif Td >= C['TBp']:
        HD = C['mp2'] * Td + C['cp2']

    # calculate the heat demand for the given number of dwellings
    return HD * total_dwellings_pattern

def LA_heat_pattern_totals(future_year, FES, scenario):
    """
    Calculate the heat demand for a given Local Authority, year, FES year, and FES scenario.
    """
    # Get the FES heat supply data for the given year, FES and scenario
    df = FES_heat_supply_data.year_FES_heat_supply(future_year, FES, scenario)
    df.columns = df.columns.str.replace(r'stock ', '')
    df.index = df.index.str.replace(r'Chiltern District', 'Chiltern')
    df.index = df.index.str.replace(r'South Bucks District', 'South Bucks')
    df.index = df.index.str.replace(r'Wycombe District', 'Wycombe')
    df.index = df.index.str.replace(r'Aylesbury Vale District', 'Aylesbury Vale')
    list_of_tech = df.columns.values[4:18]

    # calculate the mix of daytime, bi-modal, and continuous heat demand profiles based on technology mixes (numbers are percentages)
    heating_pattern_to_tech = {'ASHP': {'daytime': 30, 'bi-modal': 9, 'continuous': 61},
                               'GSHP': {'daytime': 21, 'bi-modal': 5, 'continuous': 74},
                               'Gas boiler': {'daytime': 46, 'bi-modal': 34, 'continuous': 20}}

    LAs = pd.read_csv('data/LA_UK/air_temp/air_temp_2012.csv', index_col=0).columns
    dict_LA = {}    
    for LA in LAs:
        df_heat_pattern = pd.DataFrame(heating_pattern_to_tech)
        #list of tech without existing tech in df above
        list_of_tech_ = np.delete(list_of_tech, np.where(list_of_tech == 'ASHP'))
        list_of_tech_ = np.delete(list_of_tech_, np.where(list_of_tech == 'GSHP'))
        list_of_tech_ = np.delete(list_of_tech_, np.where(list_of_tech == 'Gas boiler'))
        list_of_tech_ = np.delete(list_of_tech_, np.where(list_of_tech == 'Electric storage'))
        # assume that most tech will be run like gas boiler
        for i in list_of_tech_:
            df_heat_pattern[i] = {'daytime': 46, 'bi-modal': 34, 'continuous': 20}
        # closest since no night pattern is in this dataset
        df_heat_pattern['Electric storage'] = {'daytime': 0, 'bi-modal': 0, 'continuous': 100}
        df_heat_pattern['Hybrid (ASHP + Electric resistive)'] = {'daytime': 46, 'bi-modal': 34, 'continuous': 20}
        # total tech mix in the LA
        df_heat_pattern = df_heat_pattern.T / 100
        for tech in list_of_tech:
            df_heat_pattern.loc[tech] = df.loc[LA, list_of_tech][tech] * df_heat_pattern.loc[tech]
        dict_LA[LA] = df_heat_pattern
    # heat_pattern_totals = df_heat_pattern.sum()

    # print(df_heat_pattern)

    return dict_LA

def calc_LA_average_day_temperature(day, year, LA):
    """
    Calculate the average day temperature for a given day (between 1 and 365 or 366), using historic year.
    """
    # read in the temperature data
    df = pd.read_csv('data/LA_UK/air_temp/air_temp_' + str(year) + '.csv', index_col=0)
    df.index = pd.to_datetime(df.index)
    df = df.loc[df.index.year == year]
    df = df.loc[df.index.dayofyear == day]
    df = df.loc[:, LA]

    # calculate the average temperature for the day
    average_day_temperature = df.mean()

    return average_day_temperature

def calc_LA_year_average_day_temperature(year_historical, LA):
    # average day temp for each day
    # check number of days in year

    # read in the temperature data
    df = pd.read_csv('data/LA_UK/air_temp/air_temp_' + str(year_historical) + '.csv', index_col=0)
    df.index = pd.to_datetime(df.index)
    df = df.loc[df.index.year == year_historical]

    daysinyear = 365 + calendar.isleap(year_historical)
    day_temps = {}
    for day in range(1, daysinyear + 1):
    # for day in range(1, 4):
        df_temps = df.loc[df.index.dayofyear == day]
        df_temps = df_temps.loc[:, LA]
        # calculate the average temperature for the day
        day_temps[day] = df_temps.mean()

    day_temps = pd.Series(day_temps)
    day_temps.name = LA

    return day_temps

def save_all_LA_year_average_day_temperature():

    for year in range(2010, 2022 + 1):
        print(year)
        # get a list of LA
        df = pd.read_csv('data/LA_UK/air_temp/air_temp_' + str(year) + '.csv', index_col=0)
        data = []
        for LA in df.columns:
            data.append(calc_LA_year_average_day_temperature(year, LA))
        df_output = pd.DataFrame(data).T
        df_output.to_csv('outputs/LA_UK/air_temp/average_day_air_temp_' + str(year) + '.csv')


def LA_air_temperature(year):
    """
    Extract the air temperature from Atlite for all Local Authorities and year.
    """

    df = pd.read_excel('data/LA_UK/uk_LA_locations.xlsx', sheet_name='uk_local_authorities_future')#, index_col=0)
    # df['nice-name'] = df['nice-name'].map(lambda x: x.lstrip('+-').rstrip(' District'))
    # df['nice-name'] = df['nice-name'].str.replace(' District', '')
    df = df[['nice-name', 'lat', 'long']].set_index('nice-name')
    df.index.name = 'Local_Authority'
    # print(df.head(20))

    df_FES = FES_heat_supply_data.year_FES_heat_supply(2021, '2021', scenario='LW')
    df_FES.index = df_FES.index.str.replace(' District', '')

    for L_A in df_FES.index:
        df_FES.loc[L_A, 'lon'] = df.loc[L_A, 'long']
        df_FES.loc[L_A, 'lat'] = df.loc[L_A, 'lat']

    df_FES = df_FES[['lon', 'lat']]
    df_FES.index.name = 'name'
    df_FES.columns = ['y', 'x']
    df_FES['capacity'] = 1

    # then use atlite to get the air temperature for the given LA
    # read in cutout
    shpfilename = shpreader.natural_earth(resolution='10m',
                                          category='cultural',
                                          name='admin_0_countries')
    reader = shpreader.Reader(shpfilename)
    UK = gpd.GeoSeries({r.attributes['NAME_EN']: r.geometry
                        for r in reader.records()},
                       crs={'init': 'epsg:4326'}).reindex(['United Kingdom'])

    # Define the cutout; this will not yet trigger any major operations
    file = 'uk-' + str(year) + '.nc'
    time = str(year)
    path = '../atlite/cutouts/' + file
    cutout = atlite.Cutout(path=path,
                           module="era5",
                           bounds=UK.unary_union.bounds,
                           time=time)
    # This is where all the work happens
    # (this can take some time, for us it took ~15 minutes).
    # features = ['height', 'wnd100m', 'wnd_azimuth', 'roughness', 'influx_toa',
    #         'influx_direct', 'influx_diffuse', 'albedo', 'solar_altitude',
    #         'solar_azimuth', 'temperature', 'runoff']
    cutout.prepare()

    # USE A DATAFRAME WITH ALL LA BY 'NAME', 'LON', 'LAT' AND CAPACITY WITH VALUE 1

    sites = df_FES
    nearest = cutout.data.sel({"x": sites.x.values, "y": sites.y.values}, "nearest").coords
    sites["x"] = nearest.get("x").values
    sites["y"] = nearest.get("y").values
    cells = cutout.grid
    cells_generation = sites.merge(cells, how="inner").rename(pd.Series(sites.index))

    # duplicate_rows = cells_generation.duplicated(subset=['y', 'x'])
    # print(duplicate_rows)

    # count = len(duplicate_rows[duplicate_rows == True])
    # print(count, 'counting')

    cells_generation1 = cells_generation.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation1.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp1 = cutout.temperature(
        layout=layout, shapes=cells_generation1.geometry
    ).to_pandas()

    cells_generation2 = cells_generation.drop_duplicates(subset=['y', 'x'], keep='last')
    layout = (
        xr.DataArray(cells_generation2.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp2 = cutout.temperature(
        layout=layout, shapes=cells_generation2.geometry
    ).to_pandas()

    cells_generation3 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation3 = cells_generation3[~(cells_generation3.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation3.duplicated(subset=['y', 'x']))]
    cells_generation3 = cells_generation3.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation3.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp3 = cutout.temperature(
        layout=layout, shapes=cells_generation3.geometry
    ).to_pandas()

    cells_generation4 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation4 = cells_generation4[~(cells_generation4.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation4.duplicated(subset=['y', 'x']))]
    cells_generation4 = cells_generation4[~(cells_generation4.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation4.duplicated(subset=['y', 'x']))]
    cells_generation4 = cells_generation4.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation4.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp4 = cutout.temperature(
        layout=layout, shapes=cells_generation4.geometry
    ).to_pandas()

    cells_generation5 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation5 = cells_generation5[~(cells_generation5.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation5.duplicated(subset=['y', 'x']))]
    cells_generation5 = cells_generation5[~(cells_generation5.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation5.duplicated(subset=['y', 'x']))]
    cells_generation5 = cells_generation5[~(cells_generation5.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation5.duplicated(subset=['y', 'x']))]
    cells_generation5 = cells_generation5.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation5.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp5 = cutout.temperature(
        layout=layout, shapes=cells_generation5.geometry
    ).to_pandas()

    cells_generation6 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation6 = cells_generation6[~(cells_generation6.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation6.duplicated(subset=['y', 'x']))]
    cells_generation6 = cells_generation6[~(cells_generation6.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation6.duplicated(subset=['y', 'x']))]
    cells_generation6 = cells_generation6[~(cells_generation6.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation6.duplicated(subset=['y', 'x']))]
    cells_generation6 = cells_generation6[~(cells_generation6.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation6.duplicated(subset=['y', 'x']))]
    cells_generation6 = cells_generation6.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation6.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp6 = cutout.temperature(
        layout=layout, shapes=cells_generation6.geometry
    ).to_pandas()

    cells_generation7 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation7 = cells_generation7[~(cells_generation7.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation7.duplicated(subset=['y', 'x']))]
    cells_generation7 = cells_generation7[~(cells_generation7.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation7.duplicated(subset=['y', 'x']))]
    cells_generation7 = cells_generation7[~(cells_generation7.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation7.duplicated(subset=['y', 'x']))]
    cells_generation7 = cells_generation7[~(cells_generation7.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation7.duplicated(subset=['y', 'x']))]
    cells_generation7 = cells_generation7[~(cells_generation7.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation7.duplicated(subset=['y', 'x']))]
    cells_generation7 = cells_generation7.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation7.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp7 = cutout.temperature(
        layout=layout, shapes=cells_generation7.geometry
    ).to_pandas()

    cells_generation8 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8[~(cells_generation8.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation8.duplicated(subset=['y', 'x']))]
    cells_generation8 = cells_generation8.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation8.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp8 = cutout.temperature(
        layout=layout, shapes=cells_generation8.geometry
    ).to_pandas()

    cells_generation9 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9[~(cells_generation9.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation9.duplicated(subset=['y', 'x']))]
    cells_generation9 = cells_generation9.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation9.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp9 = cutout.temperature(
        layout=layout, shapes=cells_generation9.geometry
    ).to_pandas()

    cells_generation10 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10[~(cells_generation10.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation10.duplicated(subset=['y', 'x']))]
    cells_generation10 = cells_generation10.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation10.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp10 = cutout.temperature(
        layout=layout, shapes=cells_generation10.geometry
    ).to_pandas()

    cells_generation11 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11[~(cells_generation11.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation11.duplicated(subset=['y', 'x']))]
    cells_generation11 = cells_generation11.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation11.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp11 = cutout.temperature(
        layout=layout, shapes=cells_generation11.geometry
    ).to_pandas()

    cells_generation12 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12[~(cells_generation12.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation12.duplicated(subset=['y', 'x']))]
    cells_generation12 = cells_generation12.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation12.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp12 = cutout.temperature(
        layout=layout, shapes=cells_generation12.geometry
    ).to_pandas()

    cells_generation13 = cells_generation[cells_generation.duplicated(subset=['y', 'x'], keep=False)]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13[~(cells_generation13.duplicated(subset=['y', 'x'], keep=False) ^ cells_generation13.duplicated(subset=['y', 'x']))]
    cells_generation13 = cells_generation13.drop_duplicates(subset=['y', 'x'], keep='first')
    layout = (
        xr.DataArray(cells_generation13.fillna(0.0).set_index(["y", "x"]).capacity.unstack())
        # .reindex_like(cap_factors)
        # .rename("Installed Capacity [MW]")
    )
    air_temp13 = cutout.temperature(
        layout=layout, shapes=cells_generation13.geometry
    ).to_pandas()

    air_temp = pd.concat([air_temp1, air_temp2, air_temp3, air_temp4, air_temp5, air_temp6, air_temp7, air_temp8, air_temp9, air_temp10, air_temp11, air_temp12, air_temp13], axis=1)
    air_temp = air_temp.loc[:,~air_temp.columns.duplicated()].copy()

    print(air_temp)
    file = 'data/LA_UK/air_temp/air_temp_' + str(year) + '.csv'
    air_temp.to_csv(file)

if __name__ == '__main__':

    # for year in range(2010, 2022 + 1):
    #     LA_air_temperature(year)
    # LA_air_temperature(2010)
    # LA_heat_demand_heat_pump('Aberdeen City', 2045, '2021', 'ST')
    # Td = calc_LA_average_day_temperature(5, 2012, 'Aberdeen City')
    # LA_heat_pattern_totals('Aberdeen City', 2025, '2021', 'ST')
    # heat_demand_for_LA_tech_for_one_day(
    #     LA='Aberdeen City', dayofyear=5, weather_year=2012,
    #      future_year=2045, FES='2021', scenario='ST')
    # heating_pattern = 'daytime'
    # print(heat_demand_for_one_pattern_for_one_day(dwellings[heating_pattern], heating_pattern, Td))
    # heat_demand_for_LA_tech('Aberdeen City', 2012, 2045, '2021', 'ST')
    # half_hourly_profiles('daytime', -4)
    # save_average_day_temperature(year_historical=2012, LA='Aberdeen City')
    # save_all_LA_year_average_day_temperature()
    # heat_demand_for_LA_daily('Aberdeen City', 2012, 2045, '2022', 'ST')
    # heat_demand_for_LA_half_hourly('Chiltern', 2010, 2024, '2021', 'LW')
    # heat_demand_for_all_variables_LA_half_hourly(weather_year=2012, future_year=2050, FES='2022', scenario='LW')
    FES_scaling_factor_calc(2050, '2022', 'LW')
