import pandas as pd
import numpy as np

def read_FES_heat_supply(FES):

    if FES == '2021':
        dfs = []
        for year in ['2020', '2025', '2030', '2035']:
            file = 'data/FES Spatial Heat Model/' + FES + '/la_level_outputs_' + year + '_domestic_all_scenarios_org_updated.csv'
            df_FES = pd.read_csv(file, index_col=1)
            dfs.append(df_FES)
        df = pd.concat(dfs).fillna(0)

    elif FES == '2022':
        dfs = []
        for year in ['2020', '2025', '2030', '2035', '2040', '2045', '2050']:
            file = 'data/FES Spatial Heat Model/' + FES + '/fes22_la_level_outputs_' + year + '_domestic_all_scenarios.csv'
            df_FES = pd.read_csv(file, index_col=1)
            dfs.append(df_FES)
        df = pd.concat(dfs).fillna(0)
    
    return df

def year_FES_heat_supply(year, FES, scenario=None):

    if FES == '2021':
        year_list = np.array([2020, 2025, 2030, 2035])
        closest_year = year_list[year_list <= year].max()
    
    elif FES == '2022':
        year_list = np.array([2020, 2025, 2030, 2035, 2040, 2045, 2050])
        closest_year = year_list[year_list <= year].max()

    df = read_FES_heat_supply(FES)
    df = df.loc[df['Year'] == closest_year]
    df = df.loc[df['Scenario'] == scenario]

    return df

if __name__ == '__main__':
    year_FES_heat_supply(2031, '2021', scenario='LW')
