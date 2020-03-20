import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_string_dtype, is_numeric_dtype

def get_data():
    df = pd.read_csv('../resultset.csv', sep=";")
    columns = get_columns()
    df = df[columns]
    # df['categoty'], df['info'], df['product'] = df['name'].str.split(', ', 2).str # NOTE: This is dangerous because it creates several NaN values
    # df.drop('name', axis=1, inplace=True)
    df, df_clean, df_no_nan = clean_data(df)
    # logging.info('Data imported and cleaned')
    return df, df_clean, df_no_nan

def ensure_format(df, col_name):
    if is_string_dtype(df[col_name]):
        return pd.to_numeric(df[col_name].map(lambda x: x if x != '<0.1' else 0 )) # NOTE: the estimate <0.1 creates a distortion in the data. Hence, removed.
    elif is_numeric_dtype(df[col_name]):
        return df[col_name]
    else:
        raise Exception('Data is not correct format (number or string)')

def clean_column(df, col_name):
    if is_string_dtype(df[col_name]):
        col = pd.to_numeric(df[col_name].map(lambda x: x if x != '<0.1' else 0 )) # NOTE: the estimate <0.1 creates a distortion in the data. Hence, removed.
    return col.replace([np.inf, -np.inf], np.nan).fillna(0)


def clean_data(df):
    df['kcal'] = ensure_format(df, 'energy,calculated (kJ)') / 4.184 # NOTE: kJ -> kcal
    df['fat_kcal'] = ensure_format(df, 'fat, total (g)') * 9
    df['carb_kcal'] = ensure_format(df, 'carbohydrate, available (g)') * 4
    df['protein_kcal'] = ensure_format(df, 'protein, total (g)') * 4
    df['alc_kcal'] = ensure_format(df, 'alcohol (g)') * 7
    df['sugar'] = ensure_format(df, 'sugars, total (g)')
    df['fibre'] = ensure_format(df, 'fibre, total (g)')
    df['alc'] = ensure_format(df, 'alcohol (g)')
    df['sodium'] = clean_column(df, 'sodium (mg)')
    df['salt'] = clean_column(df, 'salt (mg)')
    df['kcal_ratio'] = (df['kcal'] / (df['fat_kcal'] + df['carb_kcal'] + df['protein_kcal'] + df['alc_kcal']))
    df_no_nan = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["kcal_ratio"])
    df_clean = df_no_nan[df_no_nan.kcal_ratio <= 1.3]

    # df['kj'] = ensure_format(df, 'energy,calculated (kJ)')
    # df['fat_kj'] = ensure_format(df, 'fat, total (g)') * 38
    # df['carb_kj'] = ensure_format(df, 'carbohydrate, available (g)') * 17
    # df['protein_kj'] = ensure_format(df, 'protein, total (g)') * 17
    # df['alc_kj'] = ensure_format(df, 'alcohol (g)') * 30
    # df['kj_ratio'] = (df['kj'] / (df['fat_kj'] + df['carb_kj'] + df['protein_kj'] + df['alc_kj']))
    # df_no_nan = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["kj_ratio"])
    # df_clean = df_no_nan[df_no_nan.kj_ratio <= 1.3]

    df_clean = df_clean[df_clean.alc <= 0.4]
    return df, df_clean, df_no_nan

def get_columns():
    
    essentials = [ 
        'name', 
        'energy,calculated (kJ)', # 1 kJ == 0.239006 kcal # 1/4.184 kJ = 1 kcal
        'fat, total (g)', 
        'carbohydrate, available (g)', 
        'protein, total (g)', 
        'fibre, total (g)', 
        'sugars, total (g)', 
        'alcohol (g)', # # NOTE: extra: no ALCOHOL
        'sodium (mg)', # NOTE: extra: low salt
        'salt (mg)', # NOTE: extra: low salt (lot of sports) MAX 5g/d (lapset 3g/d)
    ]

    # 1 Portion = 100g
    all_usefull = [
        'id', 
        'name', 
        'energy,calculated (kJ)', # 1 kJ == 0.239006 kcal # 1/4.184 kJ = 1 kcal
        'fat, total (g)', 
        'carbohydrate, available (g)', 
        'protein, total (g)', 
        'fibre, total (g)', 
        'sugars, total (g)', 
        'alcohol (g)', # # NOTE: extra: no ALCOHOL
        'lactose (g)', # NOTE: extra: allergies  
        'cholesterol (GC) (mg)', # NOTE: extra: low colesterol  
        'calcium (mg)', # NOTE: extra: pregnant
        'iron, total (mg)', # NOTE: extra: pregnant or dizzy
        'magnesium (mg)', # NOTE: extra: lot of sports 
        'sodium (mg)', # NOTE: extra: low salt
        'salt (mg)', # NOTE: extra: low salt (lot of sports) MAX 5g/d (lapset 3g/d)
        'zinc (mg)', # NOTE: extra: feeling sick
        'vitamin C (ascorbic acid) (mg)', # NOTE: extra: feeling sick
        'vitamin B-12 (cobalamin) (µg)', # NOTE: extra: vegetarian
        'vitamin D (µg)', # NOTE: extra: winter time 
    ]
    # NOTE: allergies # Keliaakikko voi syödä kaikkia ruokia, joiden valmistuksessa ei ole käytetty vehnää, ohraa ja ruista. Keliaakikolle sopivia viljoja ovat gluteenittomat viljat eli riisi, maissi, hirssi ja tattari. Lisäksi keliaakikot voivat käyttää kauraa.
    # NOTE: allergies # Pähkinä

    return essentials