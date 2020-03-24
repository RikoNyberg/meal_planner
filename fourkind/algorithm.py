import pandas as pd
import numpy as np
from scipy.optimize import linprog
from pulp import *
# import logging
import data_import
import time


class DailyMealPlan():
    def __init__(self, meals, limits={}, prev_meal_plan=None, used_meals=None, integer=False, day='monday'):
        self.daily_meal_plan_calculated = False
        self.df = meals.copy()  # The df of food items
        self.integer = integer  # Is the meal_plan quantities calculated as int or continuous
        self.day = day

        print(f'All Meals:   {len(self.df)}')
        print(
            f'Used Meals:  {len(used_meals if used_meals is not None else [])}')
        if used_meals is not None:
            self.df.drop(used_meals.index, inplace=True)
        print(f'All - Used = {len(self.df)}')

        if prev_meal_plan != None:
            self.remove_previous_meal_plan_categories(prev_meal_plan)

        def get_limit(limit_name, default, limits_dict):
            return default if not limits_dict.get(limit_name) else limits_dict[limit_name]

        # Mandatory
        self.fibre_limit = get_limit('fibre_limit', 21, limits)
        self.kcal_limit = get_limit('kcal_limit', 2000, limits)
        self.carb_kcal_limit = get_limit('carb_kcal_limit', 1000, limits)
        self.protein_kcal_limit = get_limit('protein_kcal_limit', 600, limits)
        self.fat_kcal_limit = get_limit('fat_kcal_limit', 400, limits)

        # Extra
        self.salt_limit = get_limit('salt_limit', 5000, limits)
        self.sodium_limit = get_limit('sodium_limit', 1500, limits)

    def remove_previous_meal_plan_categories(self, prev_meal_plan):
        prev_df = prev_meal_plan.get_optimal_meal_plan()[
            ['category', 'extra_category']]

        prev_cat = prev_df['category'].tolist()
        self.df = self.df[~self.df['category'].isin(prev_cat)]

        prev_extra_cat = list(
            filter(lambda a: a != '', prev_df['extra_category'].tolist()))
        self.df = self.df[~self.df['extra_category'].isin(prev_extra_cat)]

    def calculate_optimal_meal_plan_continuous(self):
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
        salt = self.df['salt']  # (mg)
        sodium = self.df['sodium']  # (mg)

        A_upperbounds = np.array([
            count, -fibre, sodium, salt
        ])
        b_upperbounds = np.array([
            10, -self.fibre_limit, self.sodium_limit, self.salt_limit
        ])
        A_equality = np.array([kcal, carb_kcal, protein_kcal, fat_kcal])
        b_equality = np.array([
            self.kcal_limit, self.carb_kcal_limit, self.protein_kcal_limit, self.fat_kcal_limit
        ])
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

    def calculate_optimal_meal_plan(self):
        self.df['count'] = 1
        # Mandatory
        sugar = self.df['sugar']
        fibre = self.df['fibre']
        kcal = self.df['kcal']
        carb_kcal = self.df['carb_kcal']
        protein_kcal = self.df['protein_kcal']
        fat_kcal = self.df['fat_kcal']

        # Extra
        salt = self.df['salt']  # (mg)
        sodium = self.df['sodium']  # (mg)
        count = self.df['count']

        # Creates a list of the ingredients
        ingredients = self.df.index.tolist()

        # Problem ('prob') variable to contain the problem data
        prob = LpProblem("Optimal Meal Plan", LpMinimize)

        # A dictionary called 'ingredient_vars' is created to contain the referenced Variables
        if self.integer:
            # logger.info("Calculating the meal plan with Integer Linear Programming so this might take a while (hours)...")
            ingredient_vars = LpVariable.dicts(
                "grams", ingredients, 0, 5, cat='Integer')
        else:
            # logger.info("Calculating the meal plan with Continuous functions, should take 5 to 10 minutes...")
            ingredient_vars = LpVariable.dicts(
                "grams", ingredients, 0, 5, cat='Continuous')

        # The objective function is added to 'prob' first
        prob += lpSum([sugar[i]*ingredient_vars[i]
                       for i in ingredients]), "Total_Sugar_of_Meal_Plan"

        # The five constraints are added to 'prob'

        prob += lpSum([kcal[i] * ingredient_vars[i]
                       for i in ingredients]) <= self.kcal_limit, "kcal_sum"
        prob += lpSum([carb_kcal[i] * ingredient_vars[i]
                       for i in ingredients]) == self.carb_kcal_limit, "carb_kcal_sum"
        prob += lpSum([protein_kcal[i] * ingredient_vars[i]
                       for i in ingredients]) == self.protein_kcal_limit, "protein_kcal_sum"
        prob += lpSum([fat_kcal[i] * ingredient_vars[i]
                       for i in ingredients]) == self.fat_kcal_limit, "fat_kcal_sum"

        prob += lpSum([fibre[i] * ingredient_vars[i]
                       for i in ingredients]) >= self.fibre_limit, "fibre_requirement"

        prob += lpSum([count[i] * ingredient_vars[i]
                       for i in ingredients]) <= 10, "count_requirement"
        prob += lpSum([sodium[i] * ingredient_vars[i]
                       for i in ingredients]) <= self.sodium_limit, "sodium_requirement"
        prob += lpSum([salt[i] * ingredient_vars[i]
                       for i in ingredients]) <= self.salt_limit, "salt_requirement"

        prob.solve()

        # Each of the variables is printed with it's resolved optimum value
        ingr_grams = []
        i = 0
        for v in prob.variables():
            ingr_grams.append(v.varValue * 100)
            if v.varValue:
                i += 1
        print(i)

        self.df['grams'] = ingr_grams
        self.daily_meal_plan_calculated = True

    def get_optimal_meal_plan(self):
        if not self.daily_meal_plan_calculated:
            # logger.info("Optimizing today's meal plan...")
            # self.calculate_optimal_meal_plan()
            self.calculate_optimal_meal_plan_continuous()
        info = ['name', 'count', 'grams', 'kcal', 'sugar', 'fibre', 'carb_kcal',
                'protein_kcal', 'fat_kcal', 'salt', 'sodium', 'category', 'extra_category']
        df = self.df[info].copy()

        # Calculating meal plans nutrient quantities for each food
        nutrients = ['fibre', 'sugar', 'kcal', 'carb_kcal',
                     'protein_kcal', 'fat_kcal', 'salt', 'sodium']
        # Rounding to nearest 10g and each nutrient is per 100g
        df_grams = df['grams'].round(-1).div(100)
        df[nutrients] = df[nutrients].multiply(df_grams, axis='index')
        df.sort_values(by='grams', ascending=False, inplace=True)

        df = df[df['grams'] <= 10]  # taking only recommendations over 10 grams
        df['grams'] = df['grams'].round(-1)  # Rounding to nearest 10g
        return df

    def get_total_nutrients(self):
        columns = ['count', 'grams', 'fibre', 'sugar', 'kcal',
                   'carb_kcal', 'protein_kcal', 'fat_kcal', 'salt', 'sodium']
        return self.get_optimal_meal_plan()[columns].sum()

    def save_total_nutrients_to_csv(self):
        self.get_total_nutrients().to_csv(
            f'meal_plans/{self.day}_nutrients.csv')

    def save_meal_plan_to_csv(self):
        self.get_optimal_meal_plan().to_csv(
            f'meal_plans/{self.day}_meal_plan.csv')


df = data_import.get_data()
df = data_import.clean_data(df)

previous_day = None
used_meals = None
start = time.time()
for day_name in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
    day = DailyMealPlan(
        df, day=day_name, prev_meal_plan=previous_day, used_meals=used_meals)
    print('-'*20, day_name.upper(), '-'*20)
    meal_plan = day.get_optimal_meal_plan()
    print(meal_plan)

    used_meals = pd.concat([used_meals, meal_plan])
    day.save_meal_plan_to_csv()
    day.save_total_nutrients_to_csv()
    print(day.get_total_nutrients())
    previous_day = day

end = time.time()
print('-'*50, 'Running time:', end - start)
