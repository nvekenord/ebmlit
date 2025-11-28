import pandas as pd
from ebm import extractors
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.s_curve import calculate_s_curves
from ebm.model import area as a_f
from ebm.model import energy_need as e_n
from ebm.model import energy_use as e_u
from ebm.model import heating_systems_parameter as h_s_param
import streamlit as st

years = YearRange(2020, 2050)
database_manager = DatabaseManager()

scurve_parameters = database_manager.get_scurve_params() # 📍

area_parameters = database_manager.get_area_parameters() # 📍
area_parameters['year'] = years.start

building_code_parameters = database_manager.file_handler.get_building_code() # 📍

s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years) # 📌
area_forecast = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters, area_parameters, database_manager) # 📍
energy_need_kwh_m2 = extractors.extract_energy_need(years, database_manager) # 📍
heating_systems_projection = extractors.extract_heating_systems_forecast(years, database_manager) # 📍
energy_use_holiday_homes = extractors.extract_energy_use_holiday_homes(database_manager) # 📍

total_energy_need = e_n.transform_total_energy_need(energy_need_kwh_m2, area_forecast)  # 📌
heating_systems_parameter = h_s_param.heating_systems_parameter_from_projection(heating_systems_projection) # 📌
energy_use_kwh = e_u.building_group_energy_use_kwh(heating_systems_parameter, total_energy_need) # 📌

area_change = a_f.transform_area_forecast_to_area_change(area_forecast=area_forecast, building_code_parameters=building_code_parameters)

demolition_construction_long = a_f.transform_demolition_construction(energy_use_kwh, area_change)

df = demolition_construction_long.set_index(['building_category', 'demolition_construction', 'year'])


building_category = st.selectbox('building_category', df.index.get_level_values(level='building_category').unique())


st.dataframe(df)

df = pd.pivot_table(df, values=['m2'], index=['building_category', 'building_code', 'year'],
                       columns=['demolition_construction'], aggfunc="sum")

st.dataframe(df)

df = df.groupby(by=['building_category', 'building_code', 'year']).sum().xs(level='building_category', key=building_category)
df = df.reset_index()
df.columns = ['building_code', 'year', 'construction', 'demolition']
st.dataframe(df)

st.bar_chart(df, x='year', y=['construction', 'demolition'])
