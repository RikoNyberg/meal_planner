import pandas as pd
import unittest
import pandera as pa

import sys
sys.path.insert(0, '..')
import data_import


class TestDataImport(unittest.TestCase):

    def test_csv_download(self):
        df = data_import.download_csv()
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
        })
        df_valid = schema_csv_download.validate(df)
        self.assertTrue(1000 in df_valid.index)

    def test_get_extra_category_list(self):
        extra_categories_test = ['chicken', 'pork', 'beef', '', 'kebab', 'fish', 'cheese', 'shrimp',
                                 'porridge', 'lamb', 'tofu', 'salmon', 'hamburger', ' ham', 'ham ', 'pasta', 'cake', 'rice', 'protein']
        df_test = pd.DataFrame(extra_categories_test, columns=['name'])
        extra_cat_created_list = data_import.get_extra_category_list(df_test)

        self.assertEqual(len(df_test), len(extra_cat_created_list))
        self.assertEqual(extra_categories_test, extra_cat_created_list)

    def test_add_necessary_columns(self):
        data = {
            'name': ['Tämä on Ruuan kategoria, ja tämä tuotemerkki Beef, ja tää on detail'],
            'energy,calculated (kJ)': [123],
            'fat, total (g)': ['3.4'],
            'carbohydrate, available (g)': ['58.8'],
            'protein, total (g)': ['<0.1'],
            'sugars, total (g)': ['1.3'],
            'fibre, total (g)': ['11.5'],
            'alcohol (g)': ['0.0'],
            'sodium (mg)': ['87.8'],
            'salt (mg)': ['470.1'],
            'lactose (g)': ['2.1'],
        }
        df_test = pd.DataFrame(data)
        df = data_import.add_necessary_columns(df_test)

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
            'kcal_ratio': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
            'lactose': pa.Column(pa.Float, pa.Check(lambda s: s >= 0)),
        })

        df_valid = schema_added_columns.validate(df)

        self.assertEqual(df_valid['kcal'][0],
                         df_test['energy,calculated (kJ)'][0]/4.184)
        self.assertEqual(df_valid['salt'][0], 470.1)
        self.assertEqual(df_valid['category'][0], 'Tämä on Ruuan kategoria')
        self.assertEqual(df_valid['extra_category'][0], 'beef')


if __name__ == '__main__':
    unittest.main()
