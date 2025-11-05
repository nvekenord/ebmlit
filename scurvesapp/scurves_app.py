
import streamlit as st
from ebm.model.building_category import BuildingCategory
from load_data import load_scurves

scurve, building_code_s_curves, df_with_area, scurve_params, building_code_parameters = load_scurves()

building_codes = ['PRE_TEK49', 'TEK49', 'TEK69', 'TEK87', 'TEK97', 'TEK10', 'TEK17']
st.set_page_config(layout="wide", page_title='EBM s curves')



select_building_category = st.sidebar.selectbox("building_category",
                                                options=[str(bc) for bc in BuildingCategory],
                                                accept_new_options=False)
st.write(f"# s-curve {select_building_category} ")

building_category = select_building_category

building_code_s_curves = building_code_s_curves.loc[select_building_category]
df_with_area = df_with_area.loc[select_building_category]
building_category_scurve_params = scurve_params.loc[select_building_category]

edited_scurve_params = st.data_editor(building_category_scurve_params)

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

