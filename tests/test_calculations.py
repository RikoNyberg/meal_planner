import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
sys.path.insert(0,'..')
from fourkind import data_import

df, df_clean, df_no_nan = data_import.get_data()
df = df.sort_values('kcal_ratio')
df_no_nan = df_no_nan.sort_values('kcal_ratio')
print(len(df))
print(len(df_no_nan))
print(len(df_clean))
df_no_nan.reset_index(drop=True, inplace=True)
print(
    '-INFO- Ratio of food that has informed energy within -10% to +30%',
    'of the calculated energy sum of macronutrients: {}%'.format(
        round(len(df_no_nan[df_no_nan.kcal_ratio <= 1.3]) / len(df) * 100, 1)))

# Save the significant outliers to get a picture what kind of outliers exist:
df_outliers = df[df.kcal_ratio > 1.3]
df_nan = df[df.isin([np.nan, np.inf, -np.inf]).any(1)]
df_outliers = pd.concat([df_outliers, df_nan])
essentials = ['name', 'energy,calculated (kJ)','fat, total (g)', 'carbohydrate, available (g)', 'protein, total (g)', 'fibre, total (g)', 'sugars, total (g)', 'alcohol (g)']
df_outliers[essentials + ['kcal_ratio']].to_csv('./assets/analytics_of_input_data/energy_vs_macronutrients-outliers.csv')
print('-INFO- Outlier count (not sufficien info or over +30%): {}/{}'.format(len(df_outliers), len(df)))

plot = df_no_nan[['kcal_ratio']].plot(
    kind='hist', 
    bins=[x * 0.1 for x in range(5, 20)], 
    title='Distribution of informed Energy and Sum of macronutrients ratio'
    )
plot.set_xlabel('Energy / Sum of macronutrients')
plt.legend().remove()
plot.get_figure().savefig('assets/analytics_of_input_data/energy_vs_macronutrients-ratio_0-2.png')



