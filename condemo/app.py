import os
import pathlib
import secrets
import time
from typing import Callable

import ebm
import pandas as pd
from ebm import extractors
from ebm.cmd.helpers import load_environment_from_dotenv, configure_loglevel
from ebm.model.file_handler import FileHandler
from loguru import logger

from ebm.__version__ import version as ebm_version
from ebm.model.data_classes import YearRange
from ebm.model.database_manager import DatabaseManager
from ebm.s_curve import calculate_s_curves
from ebm.model import area as a_f
from ebm.model import energy_need as e_n
from ebm.model import energy_use as e_u
from ebm.model import heating_systems_parameter as h_s_param
import streamlit as st

load_environment_from_dotenv()
configure_loglevel()

years = YearRange(2020, 2050)

def cache_dataframe(func: Callable, cache_dir:pathlib.Path|None=None) -> pd.DataFrame:
    if not cache_dir:
        cache_dir = pathlib.Path('cache')
    if not cache_dir.exists():
        cache_dir.mkdir()

    if 'cache_dataframe' not in st.session_state:
        st.session_state['cache_dataframe'] = secrets.token_hex(8)

    filename = cache_dir / f'condemo-{st.session_state["cache_dataframe"]}.csv'
    clean_cache(cache_dir, filename)

    if not filename.exists():
        dataframe = func()
        dataframe.to_csv(filename)
    else:
        dataframe = pd.read_csv(filename)

    return dataframe


def clean_cache(cache_dir:pathlib.Path, skip_file:pathlib.Path, delete_after_seconds: int=3600):
    """
    Clean up cache files in a directory based on age.

    Parameters
    ----------
    cache_dir : pathlib.Path
        Directory containing cache files to check.
    skip_file : pathlib.Path
        A specific file that should not be deleted.
    delete_after_seconds : int, optional
        Age threshold in seconds for deletion. Files older than this value
        will be removed. Default is 3600 (1 hour).

    Returns
    -------
    None

    Raises
    ------
    OSError
        For other OS-level errors during file operations.
    """
    logger.debug('Clean cache in {directory}', directory=cache_dir)

    for condemo_csv in cache_dir.glob('condemo-*.csv'):
        try:
            if condemo_csv != skip_file and time.time() - condemo_csv.stat().st_mtime > delete_after_seconds:
                logger.info('Deleting {filename}', filename=condemo_csv)
                condemo_csv.unlink(missing_ok=True)
            else:
                logger.debug('Not deleting {filename}', filename=condemo_csv)
        except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as ex:
            logger.debug("{exception}: {filename}", filename=condemo_csv, exception=ex)


def load_demolition_construction(database_manager:DatabaseManager) ->pd.DataFrame:
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

dm = DatabaseManager(FileHandler(directory = input_path))


df = cache_dataframe(lambda: load_demolition_construction(dm)).set_index(['building_category', 'demolition_construction', 'year']).sort_index()

available_building_categories = list(df.index.get_level_values(level='building_category').unique())
RESIDENTIAL = 'Residential'
NONRESIDENTIAL = 'Non-residential'
ALL_CATEGORIES = 'All'
available_building_groups = [RESIDENTIAL, NONRESIDENTIAL, ALL_CATEGORIES]
BOTH = 'both'
available_area_types = [BOTH, 'construction', 'demolition']
available_units = ['m2', 'gwh']

df['building_group'] = NONRESIDENTIAL
df.loc[(['apartment_block', 'house'], slice(None), slice(None)), 'building_group'] = RESIDENTIAL

page_title = 'EBM demolition and construction'

st.set_page_config(page_title=page_title)
st.markdown(f'# {page_title}')
st.markdown(f"ebm {ebm_version}")
st.markdown(f"Input from :blue-badge[{input_location}]")

building_category = st.selectbox('building_category', available_building_groups + available_building_categories)

demolition_construction = st.selectbox('area type', available_area_types)
unit = st.selectbox('unit', available_units)
years = st.multiselect('Year', years.year_range, placeholder=f'{years.start}-{years.end}')
st.markdown(f'## {building_category} {demolition_construction if not demolition_construction == BOTH else ""} {unit}')

df = pd.pivot_table(df, values=['m2', 'gwh'], index=['building_category', 'building_group', 'building_code', 'year'],
                    columns=['demolition_construction'], aggfunc="sum")

df=df.reset_index()
df.columns = ['building_category', 'building_group', 'building_code', 'year', 'construction gwh', 'demolition gwh', 'construction m2', 'demolition m2']

if building_category in (RESIDENTIAL, NONRESIDENTIAL):
    df['building_category'] = df['building_group']
elif building_category == ALL_CATEGORIES:
    df['building_category'] = ALL_CATEGORIES

df = df.groupby(by=['building_category', 'building_code', 'year']).sum().xs(level='building_category', key=building_category)

df = df.reset_index()

if years:
    year_filter = ", ".join([str(y) for y in years])
    df = df.query(f'year in [{year_filter}]')

columns = [f'construction {unit}', f'demolition {unit}'] if demolition_construction == BOTH else f'{demolition_construction} {unit}'

st.bar_chart(df, x='year', y=columns)

repo_url = 'https://github.com/nvekenord/ebmlit'
github_icon='https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'


st.markdown(
    f"""
    <a href="{repo_url}" target="_blank" style="text-decoration:none;">
        <img src="{github_icon}" width="25" style="vertical-align:middle; margin-right:8px;">ebmlit.condemo</a>
    """,
    unsafe_allow_html=True)


