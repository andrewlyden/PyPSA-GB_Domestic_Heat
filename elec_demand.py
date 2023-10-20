def electric_demand_for_heat(hd_las, LAs, df_ASHP, df_GSHP):
    """
    Calculate the electric demand for heat for all LAs
    hd_las: dictionary of heat demand for all LAs
    """

    ed_LAs = {}
    for LA in LAs:
        elec_hd_df = hd_las[LA][['ASHP', 'GSHP', 'Hybrid (ASHP + BioLPG boiler)', 'Hybrid (ASHP + Hydrogen boiler)', 'Hybrid (ASHP + Electric resistive)']]
        elec_hd_df['ASHP Elec'] = elec_hd_df['ASHP'] / df_ASHP[LA]
        # print(elec_hd_df['ASHP'])
        # print(df_ASHP[LA])
        elec_hd_df['GSHP Elec'] = elec_hd_df['GSHP'] / df_GSHP[LA]
        # assume 75% of electrical demand is met by ASHP for hybrids
        elec_hd_df['Hybrid (ASHP + BioLPG boiler) Elec'] = 0.70 * elec_hd_df['Hybrid (ASHP + BioLPG boiler)'] / df_ASHP[LA]
        elec_hd_df['Hybrid (ASHP + Hydrogen boiler) Elec'] = 0.90 * elec_hd_df['Hybrid (ASHP + Hydrogen boiler)'] / df_ASHP[LA]
        elec_hd_df['Hybrid (ASHP + Electric resistive) Elec'] = 0.90 * elec_hd_df['Hybrid (ASHP + Electric resistive)'] / df_ASHP[LA] + 0.10 * elec_hd_df['Hybrid (ASHP + Electric resistive)']

        ed_LAs[LA] = elec_hd_df[['ASHP Elec', 'GSHP Elec', 'Hybrid (ASHP + BioLPG boiler) Elec', 'Hybrid (ASHP + Hydrogen boiler) Elec', 'Hybrid (ASHP + Electric resistive) Elec']]
    
    return ed_LAs
