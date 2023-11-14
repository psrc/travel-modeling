import pandas as pd
import numpy as np
import os
import toml
import pandera as pa
from pandera import Column, Check

config = toml.load(os.path.join(os.getcwd(),'summary', 'summary_configuration.toml'))

tours_schema = pa.DataFrameSchema(
    {
        "hhno": Column(int, nullable=False),
        "pno": Column(int, nullable=False),
        "day": Column(int, nullable=False),
        "tour": Column(int, nullable=False),
        "parent": Column(int, nullable=False),
        "subtrs": Column(int, nullable=False),
        "pdpurp": Column(int, Check.isin([1,2,3,4,5,6,7,10]), nullable=False), 
        "tlvorig": Column(int, nullable=False),
        "tardest": Column(int, nullable=False),
        "tlvdest": Column(int, nullable=False),
        "tarorig": Column(int, nullable=False),
        "toadtyp": Column(int, Check.isin([1,2,3,4,5,6]), nullable=False),
        "tdadtyp": Column(int, Check.isin([1,2,3,4,5,6]), nullable=False),
        "topcl": Column(int, nullable=False),
        "totaz": Column(int, nullable=False),
        "tdpcl": Column(int, nullable=False),
        "tdtaz": Column(int, nullable=False),
        "tmodetp": Column(int, Check.isin([1,2,3,4,5,6,8,9,10]), nullable=False),
        "tpathtp": Column(int,  Check.isin([1,3,4,6,7]), nullable=False),
        "tautocost": Column(float, nullable=False),
        "tautocost": Column(float, nullable=False),
        "tautodist": Column(float, nullable=False),
        "tripsh1": Column(int, nullable=False),
        "tripsh2": Column(int, nullable=False),
        "toexpfac": Column(float, nullable=False),
    },
    coerce=True
)

trips_schema = pa.DataFrameSchema(
    {
        "hhno": Column(int, nullable=False),
        "pno": Column(int, nullable=False),
        "day": Column(int, nullable=False),
        "tour": Column(int, nullable=False),
        "half": Column(int, nullable=False),
        "tseg": Column(int, nullable=False),
        "tsvid": Column(int, nullable=False),
        "opurp": Column(int, nullable=False),
        "dpurp": Column(int, nullable=False),
        "oadtyp": Column(int, Check.isin([1,2,3,4,5,6]), nullable=False),
        "dadtyp": Column(int, Check.isin([1,2,3,4,5,6]), nullable=False),
        "opcl": Column(int, nullable=False),
        "otaz": Column(int, nullable=False),
        "dpcl": Column(int, nullable=False),
        "dtaz": Column(int, nullable=False),
        "mode": Column(int, Check.isin([1,2,3,4,5,6,8,9,10]), nullable=False),
        "pathtype": Column(int,  Check.isin([0,1,2,3,4,5,6,7]), nullable=False),
        "dorp": Column(int,Check.isin([1,2,3,9]), nullable=False),
        "deptm": Column(int, nullable=False),
        "arrtm": Column(int, nullable=False),
        # "endacttm": Column(int, nullable=False),    # Note: this should be non-null for 2023
        "travtime": Column(float, nullable=False),
        "travcost": Column(float, nullable=False),
        "travdist": Column(float, nullable=False),
        "trexpfac": Column(float, nullable=False),
    },
    coerce=True
)

household_schema = pa.DataFrameSchema(
    {
        "hhno": Column(int, nullable=False),
        "hhsize": Column(int, nullable=False),
        "hhvehs": Column(int, nullable=False),
        "hhwkrs": Column(int, nullable=False),
        "hhftw": Column(int, nullable=False),
        "hhptw": Column(int, nullable=False),
        "hhret": Column(int, nullable=False),
        "hhoad": Column(int, nullable=False),
        "hhuni": Column(int, nullable=False),
        "hhhsc": Column(int, nullable=False),
        "hh515": Column(int, nullable=False),
        "hhcu5": Column(int, nullable=False),
        "hhincome": Column(int, nullable=False),
        "hownrent": Column(int, Check.isin([1,2,3,9]), nullable=False),
        "hrestype": Column(int, Check.isin([1,2,3,4,5,6,9]), nullable=False),
        "hhtaz": Column(int, nullable=False),
        "hhparcel": Column(int, nullable=False),
        "hhexpfac": Column(float, nullable=False),
    },
    coerce=True)

person_schema = pa.DataFrameSchema(
    {
        "hhno": Column(int, nullable=False),
        "pno": Column(int, nullable=False),
        "pptyp": Column(int, Check.isin([1,2,3,4,5,6,7,8,9]), nullable=False),
        "pagey": Column(int, nullable=False),
        "pgend": Column(int, Check.isin([1,2,9]), nullable=False),
        "pwtyp": Column(int, Check.isin([0,1,2]), nullable=False),
        "pwpcl": Column(int, nullable=False),
        "pwtaz": Column(int, nullable=False),
        "pwautime": Column(float, nullable=False),
        "pwaudist": Column(float, nullable=False),
        "pstyp": Column(int, Check.isin([0,1,2]), nullable=False),
        "pspcl": Column(int, nullable=False),
        "pstaz": Column(int, nullable=False),
        "psautime": Column(float, nullable=False),
        "psaudist": Column(float, nullable=False),
        "puwmode": Column(int, Check.isin([0,1,2,3,4,5,6,7]), nullable=False),
        "puwarrp": Column(int, nullable=False),
        "puwdepp": Column(int, nullable=False),
        "ptpass": Column(int, Check.isin([0,1]), nullable=False),
        "ppaidprk": Column(int, Check.isin([0,1]), nullable=False),
        "psexpfac": Column(float, nullable=False),
    },
    coerce=True)

person_day_schema = pa.DataFrameSchema(
    {
        "hhno": Column(int, nullable=False),
        "pno": Column(int, nullable=False),
        "beghom": Column(int, nullable=False),
        "endhom": Column(int, nullable=False),
        "hbtours": Column(int, nullable=False),
        "wbtours": Column(int, nullable=False),
        "uwtours": Column(int, nullable=False),
        "wktours": Column(int, nullable=False),
        "sctours": Column(int, nullable=False),
        "estours": Column(int, nullable=False),
        "pbtours": Column(int, nullable=False),
        "shtours": Column(int, nullable=False),
        "mltours": Column(int, nullable=False),
        "sotours": Column(int, nullable=False),
        "retours": Column(int, nullable=False),
        "metours": Column(int, nullable=False),
        "wkstops": Column(int, nullable=False),
        "scstops": Column(int, nullable=False),
        "esstops": Column(int, nullable=False),
        "pbstops": Column(int, nullable=False),
        "shstops": Column(float, nullable=False),
        "mlstops": Column(float, nullable=False),
        "sostops": Column(float, nullable=False),
        "restops": Column(float, nullable=False),
        "mestops": Column(float, nullable=False),
        "wkathome": Column(int, nullable=False),
        "pdexpfac": Column(float, nullable=False),
    },
    coerce=True)

df_tour = pd.read_csv(os.path.join(config['survey_1_dir'],'_tour.tsv'), sep='\t')
df_person = pd.read_csv(os.path.join(config['survey_1_dir'],'_person.tsv'), sep='\t')
df_trip = pd.read_csv(os.path.join(config['survey_1_dir'],'_trip.tsv'), sep='\t')
df_person_day = pd.read_csv(os.path.join(config['survey_1_dir'],'_person_day.tsv'), sep='\t')
df_hh = pd.read_csv(os.path.join(config['survey_1_dir'],'_household.tsv'), sep='\t')

df_tour = tours_schema.validate(df_tour)
df_trip = trips_schema.validate(df_trip)
df_person_day = person_day_schema.validate(df_person_day)
df_person = person_schema.validate(df_person)
df_hh = household_schema.validate(df_hh)