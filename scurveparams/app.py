import os
import pathlib
from math import ceil

import ebm
import pandas as pd
import streamlit as st
from ebm.__version__ import version as ebm_version
from ebm.cmd.helpers import load_environment_from_dotenv, configure_loglevel
from ebm.model.building_category import BuildingCategory
from ebm.model.database_manager import DatabaseManager
from ebm.model.file_handler import FileHandler
try:
    from ebm.s_curve import scurve_parameters_to_scurve
except ImportError:
    from ebm.areaforecast.s_curve import scurve_from_s_curve_parameters as scurve_parameters_to_scurve


def highlight_building_category_condition(r):
    if r.name == (select_building_category, select_building_condition):
        return ['font-weight: bold'] * len(r)
    return [''] * len(r)

building_codes = ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK10', 'TEK17']
page_title = 'EBM S-Curve Parameter Editor'
st.set_page_config(layout="wide", page_title=page_title)

load_environment_from_dotenv()
configure_loglevel()

DEFAULT_PATH = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated'

input_path = pathlib.Path(os.environ.get('EBM_INPUT_DIRECTORY', DEFAULT_PATH))
input_location = input_path.name if input_path!= DEFAULT_PATH else f'(ebm default)/ {input_path.name}'
if not input_path.exists():
    raise NotADirectoryError('%s is not a directory', input_path)
if not (input_path / 's_curve.csv').is_file():
    raise FileNotFoundError('%s is not a file', input_path / 's_curve.csv')

dm = DatabaseManager(FileHandler(directory = input_path))
repo_url = 'https://github.com/nvekenord/ebmlit'
github_icon='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'

ebm_location = pathlib.Path(ebm.__path__[0])

scurve_params = dm.get_scurve_params().set_index(['building_category', 'condition'])

st.title('S Curves for ebm')

st.markdown(f"{ebm_location} :blue-badge[{ebm_version}]")
st.markdown(f"Using input from :blue-badge[{input_location}] (EBM_INPUT_DIRECTORY)")

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
    min_value=1,
    max_value=200,
    step=1)
average_age_for_measure = st.sidebar.slider(
    f'average_age_for_measure ({selected_scurve_params.average_age_for_measure})', value=st.session_state.average_age_for_measure,
    min_value=1,
    max_value=200,
    step=1)
rush_period_years = st.sidebar.slider(
    f'rush_period_years ({selected_scurve_params.rush_period_years})', value=st.session_state.rush_period_years,
    min_value=1,
    max_value=200,
    step=1)
last_age_for_measure = st.sidebar.slider(
    f'last_age_for_measure ({selected_scurve_params.last_age_for_measure})', value=st.session_state.last_age_for_measure,
    min_value=1, #min(ceil(average_age_for_measure+(rush_period_years/2))+1, 149),
    max_value=200,
    step=1)
rush_share = st.sidebar.number_input(
    f'rush_share ({selected_scurve_params.rush_share})', value=st.session_state.rush_share,
    min_value=0.0,
    max_value=1.0,
    format='%0.4f',
    step=0.01)
never_share = st.sidebar.number_input(
    f'never_share ({selected_scurve_params.never_share})', value=st.session_state.never_share,
    min_value=0.0,
    max_value=1.0,
    format='%0.4f',
    step=0.01)

# Update session_state.s_curve_params from UI
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'earliest_age_for_measure'] = earliest_age
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'average_age_for_measure'] = average_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_period_years'] = rush_period_years
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'last_age_for_measure'] = last_age_for_measure
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'rush_share'] = rush_share
st.session_state.s_curve_params.at[(select_building_category, select_building_condition), 'never_share'] = never_share

s_curves = scurve_parameters_to_scurve(st.session_state.s_curve_params.reset_index())
if 'scurve' not in s_curves.columns:
    s_curves['scurve'] = s_curves['rate_acc']
s_curves = pd.pivot_table(s_curves.reset_index(), index=['building_category', 'age'], columns=['building_condition'], values='scurve')

st.write(f"## {select_building_category.capitalize()} ")

hide_demolition = st.checkbox(label="hide demolition",
                              value=False,
                              disabled=select_building_condition == 'demolition') and select_building_condition != 'demolition'
hide_small_measure = st.checkbox(label="hide small_measure",
                                 value=False,
                                 disabled=select_building_condition == 'small_measure') and select_building_condition != 'small_measure'

hide_renovation = st.checkbox(label="hide renovation",
                              value=False,
                              disabled=select_building_condition == 'renovation') and select_building_condition != 'renovation'


st.write("### Scurves accumulated")
show_conditions = []
if not hide_demolition:
    show_conditions.append(('demolition', 'demolition_acc', '#ff4137'))
if not hide_small_measure:
    show_conditions.append(('small_measure', 'small_measure_acc', '#85c7fc'))
if not hide_renovation:
    show_conditions.append(('renovation', 'renovation_acc', '#1766c5'))

st.line_chart(s_curves.loc[select_building_category][[c[1] for c in show_conditions]], color=[c[2] for c in show_conditions],
              )

st.write("### Scurves by age")
st.line_chart(s_curves.loc[select_building_category][ [c[0] for c in show_conditions]], color=[c[2] for c in show_conditions])

# Save selected category and condition to state so that changes can be detected.
st.session_state.building_category = select_building_category
st.session_state.building_condition = select_building_condition

df = st.session_state.s_curve_params

st.write(f"""
### Python definition
```python
# {select_building_category}_{select_building_condition} =
SCurve(earliest_age={earliest_age}, 
        average_age={average_age_for_measure}, 
        rush_years={rush_period_years}, 
        rush_share={rush_share}, 
        last_age={last_age_for_measure}, 
        never_share={never_share}
        )
```
""")

st.write('## All scurve parameters')
st.dataframe(df.style.apply(highlight_building_category_condition, axis=1), height=1500, width='stretch')

# Convert to CSV
csv = df.to_csv(index=True).encode('utf-8')

st.download_button(
    label="Download s_curve_parameters.csv",
    data=csv,
    file_name="s_curve_parameters.csv",
    mime="text/csv",
)


st.markdown(
    f"""
    <a href="{repo_url}" target="_blank" style="text-decoration:none;">
        <img src="{github_icon}" width="25" style="vertical-align:middle; margin-right:8px;">ebmlit.scurveparams</a>
    """,
    unsafe_allow_html=True)

