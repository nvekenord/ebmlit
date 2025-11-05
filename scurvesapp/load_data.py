import pathlib
import os
import sys

from loguru import logger
from ebm.cmd.helpers import load_environment_from_dotenv, configure_loglevel
import ebm
import pandas as pd
from ebm.model.data_classes import YearRange

from ebm.model.database_manager import DatabaseManager
from ebm.model.file_handler import FileHandler
from ebm.model.scurve import SCurve
from ebm.model import bema

def translate_columns(columns: dict) -> dict:
    return {k.replace('_for_measure','').replace('_period_','_'): v for k,v in columns.items() if k not in ['building_category', 'condition']}

def load_scurves(scurve_parameters=None):
    filplassering = pathlib.Path(ebm.__file__).parent / 'data' / 'calibrated' / 's_curve.csv'
    dm = DatabaseManager(FileHandler(directory = filplassering.parent))

    logger.info(scurve_parameters)
    from ebm.s_curve import calculate_s_curves

    scurve_parameters = dm.get_scurve_params() if scurve_parameters is None else scurve_parameters
    building_code_parameters= dm.get_building_code_params()
    df_area = dm.get_area_parameters()
    years=YearRange(2020, 2050)

    s_curves = []

    for c in  scurve_parameters.itertuples():
        s_curve = SCurve(c.earliest_age_for_measure,
                         c.average_age_for_measure,
                         c.last_age_for_measure,
                         c.rush_period_years,
                         c.rush_share,
                         c.never_share)
        s = s_curve.calc_scurve().to_frame().reset_index()
        s.insert(0, 'building_category', c.building_category)
        s.insert(1, 'building_condition', c.condition)
        s.name = c.condition
        s_curves.append(s)

    df_scurves_bc = calculate_s_curves(scurve_parameters=scurve_parameters,
                                       building_code_parameters=building_code_parameters,
                                       years=years)

    df_scurves_bc = df_scurves_bc.reset_index()[
        ['building_category','building_code', 'year','original_condition', 'demolition', 'small_measure', 'renovation', 'renovation_and_small_measure']
    ]
    df_scurves_bc = df_scurves_bc.sort_values(by=['building_category','building_code', 'year'], key=bema.map_sort_order)

    df_scurves_bc['year'] = df_scurves_bc.year.astype(str)
    df_scurves_bc = df_scurves_bc.set_index(['building_category','building_code', 'year'], drop=True)

    q = pd.pivot_table(pd.concat(s_curves).reset_index(), index=['building_category', 'age'], columns=['building_condition'], values='scurve')

    df_area = dm.get_area_parameters().set_index(['building_category', 'building_code'])
    df_with_area = df_scurves_bc.join(df_area)

    df_with_area.loc[:, df_with_area.columns != "area"] = df_with_area.loc[:, df_with_area.columns != "area"].mul(df_with_area["area"], axis=0)

    return q, df_scurves_bc, df_with_area, scurve_parameters.set_index(['building_category', 'condition']), building_code_parameters.set_index(['building_code'], drop=True)



def main() -> None:
    load_environment_from_dotenv()
    configure_loglevel(log_format=os.environ.get('LOG_FORMAT', None))

    logger.debug(f'Starting {sys.executable} {__file__}')
    d=load_scurves()
    print(d)
    print(d[2].loc[('house', 'demolition')])




if __name__ == '__main__':
    main()





