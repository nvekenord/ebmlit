import pathlib
import sys

import streamlit as st
import ebm
from ebm.model.building_category import BuildingCategory
from load_data import load_scurves

DEFAULT_CALIBRATED = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated'
filplassering = pathlib.Path(sys.argv[1] ) if len(sys.argv) > 1 else DEFAULT_CALIBRATED



scurve, building_code_s_curves, df_with_area, scurve_params, building_code_parameters = load_scurves(input_directory=filplassering)

building_codes = ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK10', 'TEK17']
st.set_page_config(layout="wide", page_title='EBM s curves')

input_location = filplassering.name if filplassering!= DEFAULT_CALIBRATED else f'(ebm default)/ {filplassering.name}'

select_building_category = st.sidebar.selectbox("building_category",
                                                options=[str(bc) for bc in BuildingCategory],
                                                accept_new_options=False)
st.write(f"# s-curve {select_building_category} ")
st.markdown(f"Using input from :blue-badge[{input_location}]")

building_category = select_building_category

building_code_s_curves = building_code_s_curves.loc[select_building_category]
df_with_area = df_with_area.loc[select_building_category]
building_category_scurve_params = scurve_params.loc[select_building_category]

edited_scurve_params = st.data_editor(
    building_category_scurve_params,
    column_config={
        "condition": st.column_config.NumberColumn("Condition", help="building_condition", disabled=True),
        "earliest_age_for_measure": st.column_config.NumberColumn("Earliest age", help="earliest_age_for_measure"),
        "average_age_for_measure": st.column_config.NumberColumn("Average age", help="average_age_for_measure"),
        "rush_period_years": st.column_config.NumberColumn("Rush period", help="rush_period_years"),
        "last_age_for_measure": st.column_config.NumberColumn("Last age", help="last_age_for_measure"),
        "rush_share": st.column_config.NumberColumn("Rush share", help="rush_share", format="%.4f"),
        "never_share": st.column_config.NumberColumn("Never share", help="rush_share", format="%.4f"),
        })

if st.button("Reload with updated parameters"):
    scurve_params.loc[building_category, 'demolition'] = edited_scurve_params.loc['demolition']
    scurve_params.loc[building_category, 'small_measure'] = edited_scurve_params.loc['small_measure']
    scurve_params.loc[building_category, 'renovation'] = edited_scurve_params.loc['renovation']
    scurve, building_code_s_curves, df_with_area, scurve_params, building_code_parameters = load_scurves(scurve_params.reset_index())
    building_code_s_curves = building_code_s_curves.loc[building_category]
    df_with_area = df_with_area.loc[building_category]
    building_category_scurve_params = scurve_params.loc[building_category]


st.line_chart(scurve.loc[building_category][ [
    'demolition',
    'small_measure',
    'renovation',
]])

tabs = st.tabs(building_codes)

for idx, building_code in enumerate(building_codes):
    tabs[idx].write(building_code_parameters.loc[building_code])
    tabs[idx].line_chart(building_code_s_curves.loc[building_code][[
    'demolition',
    'small_measure',
    'renovation',
    'renovation_and_small_measure',
    'original_condition',
]])
    tabs[idx].write(df_with_area.loc[building_code, 'area'].iloc[0])
    tabs[idx].line_chart(df_with_area.loc[building_code][[
        'demolition',
        'small_measure',
        'renovation',
        'renovation_and_small_measure',
        'original_condition',
    ]])

#.rename(columns={'renovation': 'ren', 'demolition': 'dem', 'small_measure': 'smm', 'renovation_and_small_measure':'rsm', 'original_condition': 'o_g'}

st.dataframe(building_code_s_curves[[
    'demolition',
    'small_measure',
    'renovation',
    'renovation_and_small_measure',
    'original_condition',
]], width='stretch', height=2000)

