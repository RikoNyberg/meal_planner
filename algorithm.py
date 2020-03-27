import pandas as pd
import numpy as np
from scipy.optimize import linprog
# import logging
import data_import
import time


class DailyMealPlan():
    def __init__(self, df_meals, limits={}, prev_meal_plan=None, used_meals=None, day='monday'):
        self.daily_meal_plan_calculated = False
        self.df = df_meals.copy()  # The df of food items
        self.day = day
        self.limits = limits

        if self.limits.get('allergies')[0] == 'lactose':
            self.df = self.df[self.df['lactose'] == 0]

        print(f'All Meals:   {len(self.df)}')
        print(
            f'Used Meals:  {len(used_meals if used_meals is not None else [])}')
        if used_meals is not None:
            remove_n = int(round(len(used_meals)*0.2))
            drop_indices = np.random.choice(
                used_meals.index, remove_n, replace=False)
            used_meals.drop(drop_indices, inplace=True)
            self.df.drop(used_meals.index, inplace=True)
            print(f'Removed {remove_n} foods from the used_meals list')
        print(f'All - Used = {len(self.df)}')

        if prev_meal_plan != None:
            self.remove_previous_meal_plan_categories(prev_meal_plan)

        def get_limit(limit_name, default, limits_dict):
            return default if not limits_dict.get(limit_name) else limits_dict[limit_name]

        # Mandatory
        self.fibre_limit = get_limit('fibre_limit', 25, limits)
        self.kcal_limit = get_limit('kcal_limit', 2000, limits)
        self.carb_kcal_limit = get_limit(
            'carb_kcal_limit', self.kcal_limit*0.5, limits)
        self.protein_kcal_limit = get_limit(
            'protein_kcal_limit', self.kcal_limit*0.3, limits)
        self.fat_kcal_limit = get_limit(
            'fat_kcal_limit', self.kcal_limit*0.2, limits)

        # Extra
        if self.limits.get('low_salt'):
            self.salt_limit = get_limit('salt_limit', 5000, limits)
            self.sodium_limit = get_limit('sodium_limit', 2000, limits)

    def remove_previous_meal_plan_categories(self, prev_meal_plan):
        prev_df = prev_meal_plan.get_optimal_meal_plan()[
            ['category', 'extra_category']]

        prev_cat = prev_df['category'].tolist()
        self.df = self.df[~self.df['category'].isin(prev_cat)]

        prev_extra_cat = list(
            filter(lambda a: a != '', prev_df['extra_category'].tolist()))
        self.df = self.df[~self.df['extra_category'].isin(prev_extra_cat)]

    def calculate_optimal_meal_plan(self):
        self.df['count'] = 1
        # Mandatory
        sugar = self.df['sugar']
        fibre = self.df['fibre']
        kcal = self.df['kcal']
        carb_kcal = self.df['carb_kcal']
        protein_kcal = self.df['protein_kcal']
        fat_kcal = self.df['fat_kcal']
        count = self.df['count']

        # Extra
        if self.limits.get('low_salt'):
            salt = self.df['salt']  # (mg)
            sodium = self.df['sodium']  # (mg)

            A_upperbounds = np.array([count, -fibre, sodium, salt])
            b_upperbounds = np.array(
                [13, -self.fibre_limit, self.sodium_limit, self.salt_limit])
        else:
            A_upperbounds = np.array([count, -fibre])
            b_upperbounds = np.array([13, -self.fibre_limit])

        A_equality = np.array([
            kcal, carb_kcal, protein_kcal, fat_kcal
        ])
        b_equality = np.array(
            [self.kcal_limit, self.carb_kcal_limit, self.protein_kcal_limit, self.fat_kcal_limit])
        bounds = [(0, 5) for x in range(self.df.shape[0])]
        solution = linprog(
            c=sugar,
            A_ub=A_upperbounds,
            b_ub=b_upperbounds,
            A_eq=A_equality,
            b_eq=b_equality,
            bounds=bounds
        )
        self.df['grams'] = solution.x[solution.x > 0] * 100
        self.daily_meal_plan_calculated = True

    def get_optimal_meal_plan(self):
        if not self.daily_meal_plan_calculated:
            # logger.info("Optimizing today's meal plan...")
            self.calculate_optimal_meal_plan()
        info = ['name', 'count', 'grams', 'kcal', 'sugar', 'fibre', 'carb_kcal',
                'protein_kcal', 'fat_kcal', 'salt', 'sodium', 'category',
                'extra_category', 'lactose']
        df = self.df[info].copy()

        # Calculating meal plans nutrient quantities for each food
        nutrients = ['fibre', 'sugar', 'kcal', 'carb_kcal',
                     'protein_kcal', 'fat_kcal', 'salt', 'sodium', 'lactose']
        # Rounding to nearest 10g and each nutrient is per 100g
        df_grams = df['grams'].round(-1).div(100)
        df[nutrients] = df[nutrients].multiply(df_grams, axis='index')
        df.sort_values(by='grams', ascending=False, inplace=True)

        df = df[df['grams'] >= 10]  # taking only recommendations over 10 grams
        df['grams'] = df['grams'].round(-1)  # Rounding to nearest 10g
        return df

    def get_total_nutrients(self):
        columns = ['count', 'grams', 'fibre', 'sugar', 'kcal',
                   'carb_kcal', 'protein_kcal', 'fat_kcal', 'salt', 'sodium', 'lactose']
        return self.get_optimal_meal_plan()[columns].sum()

    def save_total_nutrients_to_csv(self):
        if self.limits.get('low_salt'):
            csv_path = f'daily_meal_plans/new_low_salt/{self.day}_nutrients_low_salt.csv'
        else:
            csv_path = f'daily_meal_plans/new/{self.day}_nutrients.csv'

        self.get_total_nutrients().to_csv(csv_path)

    def save_meal_plan_to_csv(self):
        if self.limits.get('low_salt'):
            csv_path = f'daily_meal_plans/new_low_salt/{self.day}_meal_plan_low_salt.csv'
        else:
            csv_path = f'daily_meal_plans/new/{self.day}_meal_plan.csv'
        self.get_optimal_meal_plan().to_csv(csv_path)
