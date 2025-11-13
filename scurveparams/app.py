import pathlib
from math import ceil

import ebm
import pandas as pd
import streamlit as st
from ebm.model.building_category import BuildingCategory
from ebm.model.database_manager import DatabaseManager
from ebm.model.file_handler import FileHandler
from ebm.s_curve import scurve_parameters_to_scurve

def highlight_building_category_condition(r):
    if r.name == (select_building_category, select_building_condition):
        return ['font-weight: bold'] * len(r)
    else:
        return [''] * len(r)

building_codes = ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK10', 'TEK17']
page_title = 'EBM S-Curve Parameter Editor'
st.set_page_config(layout="wide", page_title=page_title)

filplassering = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated' / 's_curve.csv'
dm = DatabaseManager(FileHandler(directory = filplassering.parent))

scurve_params = dm.get_scurve_params().set_index(['building_category', 'condition'])

st.title('S Curves for ebm')
if 'building_category' not in st.session_state:
    st.session_state.building_category = 'house'
if 'building_condition' not in st.session_state:
    st.session_state.building_condition = 'demolition'

if 's_curve_params' not in st.session_state:
    st.session_state.s_curve_params = dm.get_scurve_params().set_index(['building_category', 'condition'])

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

# If selected building_category or building_condition was changed, set column session states from s_curve_params
if st.session_state.building_category!=select_building_category or st.session_state.building_condition!=select_building_condition:
    st.session_state.earliest_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure']
    st.session_state.average_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure']
    st.session_state.rush_period_years = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years']
    st.session_state.last_age_for_measure = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure']
    st.session_state.rush_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share']
    st.session_state.never_share = st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share']
    st.session_state.building_category = select_building_category
    st.session_state.building_condition = select_building_condition

selected_scurve_params = scurve_params.loc[select_building_category, select_building_condition]

# Add s curve editor columns to UI
earliest_age = st.sidebar.slider(
    f'earliest_age ({selected_scurve_params.earliest_age_for_measure})', value=st.session_state.earliest_age_for_measure,
    min_value=1, max_value=69, step=1)
average_age_for_measure = st.sidebar.slider(
    f'average_age_for_measure ({selected_scurve_params.average_age_for_measure})', value=st.session_state.average_age_for_measure,
    min_value=1, max_value=69, step=1)
rush_period_years = st.sidebar.slider(
    f'rush_period_years ({selected_scurve_params.rush_period_years})', value=st.session_state.rush_period_years,
    min_value=1, max_value=69, step=1)
last_age_for_measure = st.sidebar.slider(
    f'last_age_for_measure ({selected_scurve_params.last_age_for_measure})', value=st.session_state.last_age_for_measure,
    min_value=ceil(average_age_for_measure+(rush_period_years/2))+1, max_value=130, step=1)
rush_share = st.sidebar.number_input(
    f'rush_share ({selected_scurve_params.rush_share})', value=st.session_state.rush_share,
    min_value=0.0, max_value=1.0, step=0.01)
never_share = st.sidebar.number_input(
    f'never_share ({selected_scurve_params.never_share})', value=st.session_state.never_share,
    min_value=0.0, max_value=1.0, step=0.01)

# Update session_state.s_curve_params from UI
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure'] = earliest_age
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure'] = average_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years'] = rush_period_years
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure'] = last_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share'] = rush_share
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share'] = never_share

s_curves = scurve_parameters_to_scurve(st.session_state.s_curve_params.reset_index())
s_curves = pd.pivot_table(s_curves.reset_index(), index=['building_category', 'age'], columns=['building_condition'], values='scurve')

st.write(f"## {select_building_category.capitalize()} ")

show_demolition = st.checkbox(label="demolition", value=True, disabled=select_building_condition=='demolition') or select_building_condition=='demolition'
show_small_measure = st.checkbox(label="small_measure", value=True, disabled=select_building_condition=='small_measure') or select_building_condition=='small_measure'
show_renovation = st.checkbox(label="renovation", value=True, disabled=select_building_condition=='renovation') or select_building_condition=='renovation'

st.write(f"### Scurves accumulated")
show_conditions = []
if show_demolition:
    show_conditions.append(('demolition', 'demolition_acc', '#ff4137'))
if show_small_measure:
    show_conditions.append(('small_measure', 'small_measure_acc', '#85c7fc'))
if show_renovation:
    show_conditions.append(('renovation', 'renovation_acc', '#1766c5'))

st.line_chart(s_curves.loc[select_building_category][[c[1] for c in show_conditions]], color=[c[2] for c in show_conditions]
              )

st.write(f"### Scurves by age")
st.line_chart(s_curves.loc[select_building_category][ [c[0] for c in show_conditions]], color=[c[2] for c in show_conditions])

# Save selected category and condition to state so that changes can be detected.
st.session_state.building_category = select_building_category
st.session_state.building_condition = select_building_condition

df = st.session_state.s_curve_params

st.write('## All scurve parameters')
st.dataframe(df.style.apply(highlight_building_category_condition, axis=1), height=1500, width='stretch')
#st.table(df.style.apply(highlight_building_category_condition, axis=1))

# Convert to CSV
csv = df.to_csv(index=True).encode('utf-8')

st.download_button(
    label="Download s_curve_parameters.csv",
    data=csv,
    file_name="s_curve_parameters.csv",
    mime="text/csv"
)
