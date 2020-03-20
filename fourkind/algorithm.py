
import pandas as pd
import numpy as np
from scipy.optimize import linprog
# import logging
import data_import

_, df_clean, _ = data_import.get_data()
df = df_clean

fibre = df['fibre']
sugar = df['sugar']
kcal = df['kcal']

carb_kcal = df['carb_kcal']
protein_kcal = df['protein_kcal']
fat_kcal = df['fat_kcal']

# Extra
salt = df['salt'] # (mg)
sodium = df['sodium'] # (mg)


A_upperbounds = np.array([-fibre, sodium, salt])
b_upperbounds = np.array([-20, 1500, 5000])
A_equality = np.array([kcal, carb_kcal, protein_kcal, fat_kcal])
b_equality = np.array([2000, 1000, 600, 400])
bounds = [(0, 5) for x in range(df.shape[0])]

solution = linprog(
    c=sugar,
    A_ub=A_upperbounds,
    b_ub=b_upperbounds,
    A_eq=A_equality,
    b_eq=b_equality,
    bounds=bounds
)

print(solution.x[solution.x > 0])
print(solution)

df['optimal_amount'] = solution.x[solution.x > 0]
essentials = ['name', 'optimal_amount', 'kcal', 'sugars, total (g)', 'energy,calculated (kJ)','fat, total (g)', 'carbohydrate, available (g)', 'protein, total (g)', 'fibre, total (g)', 'kcal_ratio', 'sodium', 'salt']
df = df[essentials]
df.to_csv('result.csv')