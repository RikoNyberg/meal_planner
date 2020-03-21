import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_string_dtype, is_numeric_dtype

def get_data():
    df = pd.read_csv('../resultset.csv', sep=";")
    wanted_columns = get_columns()
    df = df[wanted_columns]
    df = set_columns(df)

    # logging.info('Data imported and cleaned')
    return df


def clean_column(df, col_name):
    if is_string_dtype(df[col_name]):
        col = pd.to_numeric(df[col_name].map(lambda x: x if x != '<0.1' else 0 )) # NOTE: the estimate <0.1 creates a distortion in the data. Hence, removed.
    else:
        col = df[col_name]
    return col.replace([np.inf, -np.inf], np.nan).fillna(0)

def get_extra_category_list(df):
    """
    These are more general categories to improve the variety of meal plans.
    Note that short category names might get unwanted matches as the matching is really simple currently.
    E.g. 'ham' --> 'ham|burger' or 'c|ham|pignon soup'.
    Hence, be careful with these.
    """
    extra_categories = ['chicken', 'pork', 'beef', 'kebab', 'fish', 'cheese', 'shrimp', 'porridge', 'hamburger', ' ham', 'ham ', 'pasta', 'salmon', 'cake', 'lamb', 'tofu']
    extra_category_list = []

    def get_extra_category_value(row):
        for extra_c in extra_categories:
            if extra_c in row['name']:
                return extra_c
        return ''

    for i, row in df.iterrows():
        extra_category_list.append(get_extra_category_value(row))
    return extra_category_list



def set_columns(df):
    df['category'], _, _ = df['name'].str.split(', ', 2).str
    df['extra_category'] = get_extra_category_list(df)

    df['kcal'] = clean_column(df, 'energy,calculated (kJ)') / 4.184 # NOTE: kJ -> kcal
    df['fat_kcal'] = clean_column(df, 'fat, total (g)') * 9
    df['carb_kcal'] = clean_column(df, 'carbohydrate, available (g)') * 4
    df['protein_kcal'] = clean_column(df, 'protein, total (g)') * 4
    df['alc_kcal'] = clean_column(df, 'alcohol (g)') * 7
    df['sugar'] = clean_column(df, 'sugars, total (g)')
    df['fibre'] = clean_column(df, 'fibre, total (g)')
    df['alc'] = clean_column(df, 'alcohol (g)')
    df['sodium'] = clean_column(df, 'sodium (mg)')
    df['salt'] = clean_column(df, 'salt (mg)')

    df['kcal_ratio'] = (df['kcal'] / (df['fat_kcal'] + df['carb_kcal'] + df['protein_kcal'] + df['alc_kcal']))

    return df

def clean_data(df):
    """Cleaning from NaN, inf, and outliers"""
    df_no_nan = df.copy().replace([np.inf, -np.inf], np.nan).dropna(subset=["kcal_ratio"])
    df_clean = df_no_nan.copy()[df_no_nan.kcal_ratio <= 1.3] # No outliers
    df_clean = df_clean[df_clean.alc <= 0.4]
    return df_clean

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