import os
import pathlib

import ebm
from ebm.__version__ import version as ebm_version
from ebm.model import area as a_f
from ebm.model import energy_need as e_n
from ebm.model import energy_use as e_u
import pandas as pd
from ebm import extractors
from ebm.model.building_category import BuildingCategory
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.model.file_handler import FileHandler
from ebm.model import heating_systems_parameter as h_s_param
from ebm.s_curve import calculate_s_curves
import streamlit as st

@st.cache_data(show_spinner=False)
def load_demolition_construction(input_path: pathlib.Path):
    database_manager = DatabaseManager(FileHandler(directory=input_path))
    years = YearRange(2020, 2050)
    scurve_parameters = database_manager.get_scurve_params()  # 📍
    area_parameters = database_manager.get_area_parameters()  # 📍
    area_parameters['year'] = years.start
    building_code_parameters = database_manager.file_handler.get_building_code()  # 📍
    s_curves_by_condition = calculate_s_curves(scurve_parameters, building_code_parameters, years)  # 📌
    area_forecast = extractors.extract_area_forecast(years, s_curves_by_condition, building_code_parameters,
                                                     area_parameters, database_manager)  # 📍
    energy_need_kwh_m2 = extractors.extract_energy_need(years, database_manager)  # 📍
    heating_systems_projection = extractors.extract_heating_systems_forecast(years, database_manager)  # 📍
    total_energy_need = e_n.transform_total_energy_need(energy_need_kwh_m2, area_forecast)  # 📌
    heating_systems_parameter = h_s_param.heating_systems_parameter_from_projection(heating_systems_projection)  # 📌
    energy_use_kwh = e_u.building_group_energy_use_kwh(heating_systems_parameter, total_energy_need)  # 📌
    area_change = a_f.transform_area_forecast_to_area_change(area_forecast=area_forecast,
                                                             building_code_parameters=building_code_parameters)
    demolition_construction_long = a_f.transform_demolition_construction(energy_use_kwh, area_change)

    return demolition_construction_long

DEFAULT_PATH = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated'

input_path = pathlib.Path(os.environ.get('EBM_INPUT_DIRECTORY', DEFAULT_PATH))
input_location = input_path.name if input_path!= DEFAULT_PATH else f'(ebm default)/ {input_path.name}'

DEFAULT_PATH = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated'

if not input_path.exists():
    raise NotADirectoryError('%s is not a directory', input_path)
if not (input_path / 's_curve.csv').is_file():
    raise FileNotFoundError('%s is not a file', input_path / 's_curve.csv')


st.title('EBM demolition and construction')

st.markdown(f"ebm version :blue-badge[{ebm_version}]")
st.markdown(f"ebm input directory :blue-badge[{input_location}]")


with st.spinner('Loading EBM'):
    demolition_construction_long = load_demolition_construction(input_path)

available_building_categories = list(BuildingCategory)
RESIDENTIAL = 'residential'
NONRESIDENTIAL = 'non-residential'
ALL_CATEGORIES = 'all'
available_building_groups = [RESIDENTIAL, NONRESIDENTIAL, ALL_CATEGORIES]
BOTH = 'both'
available_area_types = [BOTH, 'construction', 'demolition']
available_units = ['m2', 'gwh']

default_categories = ['house', 'apartment_block', NONRESIDENTIAL]
building_category = st.sidebar.multiselect('building_category', available_building_groups + available_building_categories, default=default_categories)

df = demolition_construction_long.copy()

df['building_group'] = 'non-residential'
df.loc[df[df.building_category == 'house'].index, 'building_group'] = 'residential'
df.loc[df[df.building_category == 'apartment_block'].index, 'building_group'] = 'residential'


df['category'] = df['building_category']
if NONRESIDENTIAL in building_category:
    non_residential_index = df.query('building_category not in ["house", "apartment_block"]').index
    df.loc[non_residential_index, 'category'] = NONRESIDENTIAL
if RESIDENTIAL in building_category:
    residential_index = df.query('building_category in ["house", "apartment_block"]').index
    df.loc[residential_index, 'category'] = RESIDENTIAL
if ALL_CATEGORIES in building_category:
    df.loc[:, 'category'] = ALL_CATEGORIES

start_year, end_year = st.sidebar.slider("Select years", 2020, 2050, (2025, 2030))

available_area_types = [BOTH, 'construction', 'demolition']
demolition_construction = st.sidebar.selectbox('area type', available_area_types)

stack_categories = st.sidebar.selectbox('Chart type', options=[
    'vertical stacked',
    'horizontal stacked',
    'vertical unstacked',
    'horizontal unstacked',
])

query_category = ",".join([f"\"{c}\"" for c in building_category])

query = f'year >= {start_year} and year <={end_year} and category in [{query_category}]'

area_type_header='Demolition / construction'
if demolition_construction!=BOTH:
    query = f'{query} and demolition_construction=="{demolition_construction}"'
    area_type_header=demolition_construction

st.markdown(f'## {area_type_header}')

df = df.query(query)

chart_grouping = ['category', 'demolition_construction', 'year']
if not building_category:
    st.markdown('No building categories selected')
else:
    df: pd.DataFrame = df.groupby(by=chart_grouping, as_index=False).sum()

    for unit in ['m2', 'GWh']:
        st.markdown(f'### {unit}')
        chart_df = pd.pivot_table(df, values=[unit.lower()], index=reversed(chart_grouping),
                               aggfunc="sum").reset_index()
        st.bar_chart(chart_df,
                     x='year', y=unit.lower(), color='category'
                                         '', stack='stacked' in stack_categories,
                     horizontal='horizontal' in stack_categories)

    st.dataframe(df[['category', 'demolition_construction', 'year', 'm2', 'gwh']])


repo_url = 'https://github.com/nvekenord/ebmlit'
github_icon='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'

st.markdown(
    f"""
    <a href="{repo_url}" target="_blank" style="text-decoration:none;">
        <img src="{github_icon}" width="25" style="vertical-align:middle; margin-right:8px;">ebmlit.condemo</a>
    """,
    unsafe_allow_html=True)
