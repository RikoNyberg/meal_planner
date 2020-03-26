import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.api.types import is_string_dtype, is_numeric_dtype
import requests
import io
import pandera as pa


def get_data():
    if not os.path.exists('resultset.csv'):
        print('Downloading the dataset...')
        df = download_csv()
        df.to_csv('resultset.csv', sep=";")
    else:
        df = pd.read_csv('resultset.csv', sep=";")
        df = validate_original_csv_schema(df)
    
    wanted_columns = get_columns()
    df = df[wanted_columns]
    df = add_necessary_columns(df)
    df = drop_unwanted_food(df)
    return df


def download_csv():
    url = 'https://fineli.fi/fineli/en/elintarvikkeet/resultset.csv'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    response = requests.get(url, headers=headers)
    file_object = io.StringIO(response.content.decode('utf-8'))

    df = pd.read_csv(file_object, sep=";")
    try:
        validated_df = validate_original_csv_schema(df)
    except pa.errors.SchemaError as err:
        print('-'*20, 'ERROR', '-'*20,)
        print(f'\nProblem downloading csv from URL:\n{url}\n')
        print('-'*20, 'TO FIX THIS', '-'*20)
        print(
            '\nDownload the CSV from the URL and place it to the root folder of this project\n')
        print('-'*10, 'OR', '-'*10)
        print(f'\nCheck the error details:\n')
        print('-'*10, '\n', err, '\n', '-'*10)
    return validated_df


def validate_original_csv_schema(df):
    schema_csv_download = pa.DataFrameSchema({
        'name': pa.Column(pa.String),
        'energy,calculated (kJ)': pa.Column(pa.Int, pa.Check(
            lambda x: 0 <= x <= 4000, element_wise=True,
            error="kJ range checker [0, 2000]")),
        'fat, total (g)': pa.Column(pa.String),
        'carbohydrate, available (g)': pa.Column(pa.String),
        'protein, total (g)': pa.Column(pa.String),
        # 'fibre, total (g)': pa.Column(), # can have NaN values
        'sugars, total (g)': pa.Column(pa.String),
        'alcohol (g)': pa.Column(pa.String),
        # 'sodium (mg)': pa.Column(), # can have NaN values
        'salt (mg)': pa.Column(pa.String),
        # 'lactose (g)': pa.Column(pa.String), # can have NaN values
    })
    return schema_csv_download.validate(df)


def drop_unwanted_food(df):
    unwanted_food = [
        'Baking Yeast', 'Sweetener', 'Salt', 'Sport Beverage', 'Meal Replacement',
        'Egg White Powder', 'Gelatin', 'Flour Mixture', 'Flour', 'Baking Powder']
    return df[~df['category'].isin(unwanted_food)]
    

def clean_column(df, col_name):
    if is_string_dtype(df[col_name]):
        # NOTE: the estimate <0.1 creates a distortion in the data. Hence, removed.
        col = pd.to_numeric(df[col_name].map(
            lambda x: x if x != '<0.1' else 0.0))
    else:
        col = df[col_name]
    return col.replace([np.inf, -np.inf], np.nan).fillna(0)


def add_necessary_columns(df):
    df['category'], _ = df['name'].str.split(', ', 1).str
    df['extra_category'] = get_extra_category_list(df)

    df['kcal'] = clean_column(
        df, 'energy,calculated (kJ)') / 4.184  # kJ -> kcal
    df['fat_kcal'] = clean_column(df, 'fat, total (g)') * 9
    df['carb_kcal'] = clean_column(df, 'carbohydrate, available (g)') * 4
    df['protein_kcal'] = clean_column(df, 'protein, total (g)') * 4
    df['alc_kcal'] = clean_column(df, 'alcohol (g)') * 7
    df['sugar'] = clean_column(df, 'sugars, total (g)')
    df['fibre'] = clean_column(df, 'fibre, total (g)')
    df['alc'] = clean_column(df, 'alcohol (g)')
    df['sodium'] = clean_column(df, 'sodium (mg)')
    df['salt'] = clean_column(df, 'salt (mg)')
    df['lactose'] = clean_column(df, 'lactose (g)')
    

    df['kcal_ratio'] = (df['kcal'] / (df['fat_kcal'] +
                                      df['carb_kcal'] + df['protein_kcal'] + df['alc_kcal']))

    schema_added_columns = pa.DataFrameSchema({
        'category': pa.Column(pa.String),
        'extra_category': pa.Column(pa.String),
        'kcal': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'fat_kcal': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'carb_kcal': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'protein_kcal': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'alc_kcal': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'sugar': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'fibre': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'alc': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'sodium': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        'salt': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        # 'kcal_ratio': pa.Column(pa.Float), NOTE: might include nan values
        'lactose': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
    })

    validated_df = schema_added_columns.validate(df)
    return validated_df


def get_extra_category_list(df):
    """
    These are more general categories to improve the variety of meal plans.

    Note that the list orger matters!
    One meal can get only 1 extra category.
    E.g. "Chicken Hamburger" get chicken an not hamburger because it is first in the list.

    Also note that short category names might get unwanted matches because the matching is simple.
    E.g. 'ham' --> 'ham|burger' or 'c|ham|pignon soup'.

    Due to these restrictions be careful on what you add here and in which order.
    """
    extra_categories = ['chicken', 'pork', 'beef', 'kebab', 'fish', 'cheese', 'shrimp', 'porridge',
                        'lamb', 'tofu', 'salmon', 'hamburger', ' ham', 'ham ', 'pasta', 'cake', 'rice', 'protein']
    extra_category_list = []

    def get_extra_category_value(row):
        for extra_c in extra_categories:
            if extra_c in row['name'].lower():
                return extra_c
        return ''

    for i, row in df.iterrows():
        extra_category_list.append(get_extra_category_value(row))

    return extra_category_list


def clean_data(df):
    """Cleaning from NaN, inf, and outliers"""
    df_no_nan = df.copy().replace(
        [np.inf, -np.inf], np.nan).dropna(subset=["kcal_ratio"])
    df_clean = df_no_nan.copy()[df_no_nan.kcal_ratio <= 1.3]  # No outliers
    df_clean = df_clean[df_clean.alc <= 0.4]
    return df_clean


def get_columns():

    essentials = [
        'name',
        'energy,calculated (kJ)',
        'fat, total (g)',
        'carbohydrate, available (g)',
        'protein, total (g)',
        'fibre, total (g)',
        'sugars, total (g)',
        'alcohol (g)',  # NOTE: extra: no ALCOHOL
        'sodium (mg)',  # NOTE: extra: low salt
        'salt (mg)',  # NOTE: extra: low salt (lot of sports) MAX 5g/d (lapset 3g/d)
        'lactose (g)',  # NOTE: extra: allergies
    ]

    # 1 Portion = 100g
    all_usefull = [
        'id',
        'name',
        'energy,calculated (kJ)',
        'fat, total (g)',
        'carbohydrate, available (g)',
        'protein, total (g)',
        'fibre, total (g)',
        'sugars, total (g)',
        'alcohol (g)',  # NOTE: extra: no ALCOHOL
        'lactose (g)',  # NOTE: extra: allergies
        'cholesterol (GC) (mg)',  # NOTE: extra: low colesterol
        'calcium (mg)',  # NOTE: extra: pregnant
        'iron, total (mg)',  # NOTE: extra: pregnant or dizzy
        'magnesium (mg)',  # NOTE: extra: lot of sports
        'sodium (mg)',  # NOTE: extra: low salt
        'salt (mg)',  # NOTE: extra: low salt (lot of sports) MAX 5g/d (lapset 3g/d)
        'zinc (mg)',  # NOTE: extra: feeling sick
        'vitamin C (ascorbic acid) (mg)',  # NOTE: extra: feeling sick
        'vitamin B-12 (cobalamin) (µg)',  # NOTE: extra: vegetarian
        'vitamin D (µg)',  # NOTE: extra: winter time
    ]
    # TODO: allergies # Keliaakikko voi syödä kaikkia ruokia, joiden valmistuksessa ei ole käytetty vehnää, ohraa ja ruista. Keliaakikolle sopivia viljoja ovat gluteenittomat viljat eli riisi, maissi, hirssi ja tattari. Lisäksi keliaakikot voivat käyttää kauraa.
    # TODO: allergies # Pähkinä

    return essentials
