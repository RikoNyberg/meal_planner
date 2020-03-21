
import pandas as pd
import numpy as np
from scipy.optimize import linprog
# import logging
import data_import

class DailyMealPlan():
    def __init__(self, meals, meal_limitations={}, prev_day_meal_plan=None, day='21-3-20'):
        self.daily_meal_plan_calculated = False
        self.df = meals
        limits = meal_limitations
        self.prev_meal_plan = prev_day_meal_plan
        self.day = day

        def get_limit(limit_name, default, limits_dict):
            return default if not limits_dict.get(limit_name) else limits_dict[limit_name]

        # Mandatory
        self.fibre_limit = get_limit('fibre_limit', 20, limits)
        self.kcal_limit = get_limit('kcal_limit', 2000, limits)
        self.carb_kcal_limit = get_limit('carb_kcal_limit', 1000, limits)
        self.protein_kcal_limit = get_limit('protein_kcal_limit', 600, limits)
        self.fat_kcal_limit = get_limit('fat_kcal_limit', 400, limits)

        # Extra
        self.salt_limit = get_limit('salt_limit', 5000, limits)
        self.sodium_limit = get_limit('sodium_limit', 1500, limits)

    def calculate_optimal_meal_plan(self):

        # self.prev_meal_plan.get_optimal_meal_plan()[['category','extra_categoty']]

        # Mandatory
        sugar = self.df['sugar']
        fibre = self.df['fibre']
        kcal = self.df['kcal']
        carb_kcal = self.df['carb_kcal']
        protein_kcal = self.df['protein_kcal']
        fat_kcal = self.df['fat_kcal']

        # Extra
        salt = self.df['salt'] # (mg)
        sodium = self.df['sodium'] # (mg)

        A_upperbounds = np.array([-fibre, sodium, salt])
        b_upperbounds = np.array([
            -self.fibre_limit, self.sodium_limit, self.salt_limit
            ])
        A_equality = np.array([kcal, carb_kcal, protein_kcal, fat_kcal])
        b_equality = np.array([
            self.kcal_limit, self.carb_kcal_limit, self.protein_kcal_limit, self.fat_kcal_limit
            ])
        bounds = [(0, 5) for x in range(self.df.shape[0])] # 50 - 500g

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
        info = ['name', 'grams', 'kcal', 'sugar', 'fibre', 'carb_kcal', 'protein_kcal', 'fat_kcal', 'salt', 'sodium', 'category', 'extra_category']
        df = self.df[info].copy()

        # Calculating meal plans nutrient quantities for each food
        nutrients = ['fibre', 'sugar', 'kcal', 'carb_kcal', 'protein_kcal', 'fat_kcal', 'salt', 'sodium']
        df_grams = df['grams'].div(100)
        df[nutrients] = df[nutrients].multiply(df_grams, axis='index') # NOTE: each nutrient is per 100g
        df.sort_values(by='grams', ascending=False, inplace=True)
        
        return df[df['grams'] >= 0.1]

    def get_total_nutrients(self):
        columns = ['grams', 'fibre', 'sugar', 'kcal', 'carb_kcal', 'protein_kcal', 'fat_kcal', 'salt', 'sodium']
        return self.get_optimal_meal_plan()[columns].sum()

    def save_total_nutrients_to_csv(self):
        self.get_total_nutrients().to_csv(f'{self.day}_nutrients.csv')

    def save_meal_plan_to_csv(self):
        self.get_optimal_meal_plan().to_csv(f'{self.day}_meal_plan.csv')



df = data_import.get_data()
df = data_import.clean_data(df)
saturday = DailyMealPlan(df, day='saturday')
print(saturday.get_optimal_meal_plan())
saturday.save_meal_plan_to_csv()
saturday.save_total_nutrients_to_csv()
