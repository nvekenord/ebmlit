import pathlib
from math import ceil

import ebm
import streamlit as st
from ebm.model.building_category import BuildingCategory
from ebm.model.database_manager import DatabaseManager
from ebm.model.file_handler import FileHandler
import pandas as pd


building_codes = ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK10', 'TEK17']
st.set_page_config(layout="wide", page_title='EBM s curves')

filplassering = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated' / 's_curve.csv'
dm = DatabaseManager(FileHandler(directory = filplassering.parent))


from ebm.s_curve import calculate_s_curves, scurve_parameters_to_scurve

st.title('S Curves for ebm')
if 'building_category' not in st.session_state:
    st.session_state.building_category = 'house'
if 'building_condition' not in st.session_state:
    st.session_state.building_condition = 'demolition'

if 's_curve_params' not in st.session_state:
    st.session_state.s_curve_params = dm.get_scurve_params().set_index(['building_category', 'condition'])

def changed_building_category(**args):
    print(args, st.session_state.building_category)

select_building_category = st.sidebar.selectbox("building_category",
                                                options=[str(bc) for bc in BuildingCategory],
                                                accept_new_options=False)
select_building_condition = st.sidebar.selectbox("building_condition",
                                                options=['demolition', 'small_measure', 'renovation'],
                                                accept_new_options=False)

if 'earliest_age_for_measure' not in st.session_state:
    st.session_state.earliest_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure']
if 'average_age_for_measure' not in st.session_state:
    st.session_state.average_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure']
if 'rush_period_years' not in st.session_state:
    st.session_state.rush_period_years = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years']
if 'last_age_for_measure' not in st.session_state:
    st.session_state.last_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure']
if 'rush_share' not in st.session_state:
    st.session_state.rush_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share']
if 'never_share' not in st.session_state:
    st.session_state.never_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share']


earliest_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure']

if st.session_state.building_category!=select_building_category or st.session_state.building_condition!=select_building_condition:
    st.session_state.earliest_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure']
    st.session_state.average_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure']
    st.session_state.rush_period_years = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years']
    st.session_state.last_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure']
    st.session_state.rush_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share']
    st.session_state.never_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share']
    st.session_state.building_category = select_building_category
    st.session_state.building_condition = select_building_condition


earliest_age = st.sidebar.slider('earliest_age', min_value=1, max_value=69, step=1, value=st.session_state.earliest_age_for_measure)
average_age_for_measure = st.sidebar.slider('average_age_for_measure', min_value=1, max_value=69, step=1, value=st.session_state.average_age_for_measure)
rush_period_years = st.sidebar.slider('rush_period_years', min_value=1, max_value=69, step=1, value=st.session_state.rush_period_years)
print('min_value=', ceil(average_age_for_measure+(rush_period_years/2))+1)
last_age_for_measure = st.sidebar.slider('last_age_for_measure',
                                         min_value=ceil(average_age_for_measure+(rush_period_years/2))+1,
                                         max_value=130, step=1,
                                         value=st.session_state.last_age_for_measure)
rush_share = st.sidebar.number_input('rush_share', min_value=0.0, max_value=1.0, step=0.01, value=st.session_state.rush_share)
never_share = st.sidebar.number_input('never_share', min_value=0.0, max_value=1.0, step=0.01, value=st.session_state.never_share)

st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure'] = earliest_age
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure'] = average_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years'] = rush_period_years
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure'] = last_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share'] = rush_share
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share'] = never_share

s_curves = scurve_parameters_to_scurve(st.session_state.s_curve_params.reset_index())
s_curves = pd.pivot_table(s_curves.reset_index(), index=['building_category', 'age'], columns=['building_condition'], values='scurve')

st.write(f"# s-curve {select_building_category} ")

st.line_chart(s_curves.loc[select_building_category][ [
    'demolition_acc',
    'small_measure_acc',
    'renovation_acc'
]])

st.session_state.building_category = select_building_category
st.session_state.building_condition = select_building_condition


