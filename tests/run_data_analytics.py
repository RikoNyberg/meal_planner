import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '..')
import data_import


df = data_import.get_data()
df_no_nan = df.copy().replace([np.inf, -np.inf],
                              np.nan).dropna(subset=["kcal_ratio"])
df = df.sort_values('kcal_ratio')
df_no_nan = df_no_nan.sort_values('kcal_ratio')
df_no_nan.reset_index(drop=True, inplace=True)


print('\nRatio of food that informed energy within -10% to +30%',
      'of the calculated energy sum of its macronutrients: {}%\n'.format(
          round(len(df_no_nan[df_no_nan.kcal_ratio <= 1.3]) / len(df) * 100, 1)))


def save_outliers_to_csv(df_orig):
    '''Save the significant outliers as csv to get a picture what kind of outliers exist'''
    df = df_orig.copy()
    df_outliers = df[df.kcal_ratio > 1.3]
    df_nan = df[df.isin([np.nan, np.inf, -np.inf]).any(1)]
    df_outliers = pd.concat([df_outliers, df_nan])
    essentials = ['name', 'energy,calculated (kJ)', 'fat, total (g)', 'carbohydrate, available (g)',
                  'protein, total (g)', 'fibre, total (g)', 'sugars, total (g)', 'alcohol (g)']
    path = './assets/analytics_of_input_data/energy_vs_macronutrients-outliers.csv'
    df_outliers[essentials + ['kcal_ratio']].to_csv(path)
    print('Outlier count (not sufficien info or over +30%): {}/{}'.format(len(df_outliers), len(df)))
    print(f'Saved "energy_vs_macronutrients-outliers" chart to {path}\n')


def save_energy_difference_distribution(df_no_nan):
    '''
    Save the distribution of informed Energy and Sum of macronutrients energy difference
    to get a picture how much outliers exist
    '''
    plt.clf()
    plot = df_no_nan[['kcal_ratio']].plot(
        kind='hist',
        bins=[x * 0.1 for x in range(5, 20)],
        title='Distribution of informed Energy and Sum of macronutrients energy difference'
    )
    plot.set_xlabel('Energy / Sum of macronutrients')
    plt.legend().remove()
    path = 'assets/analytics_of_input_data/energy_vs_macronutrients-ratio_0-2.png'
    plot.get_figure().savefig(path, bbox_inches='tight')
    print(f'Saved "Energy / Sum of macronutrients" chart to {path}\n')


def print_category_size_distributions(df):
    category_dict = get_product_category_dict(df)
    print('Categories in total:', len(category_dict))
    for n in range(1, 6):
        count = 0
        for _, value in category_dict.items():
            count += 1 if value <= n else 0
        print('Food categories with {} or less food items:'.format(n), count)
    print()


def print_extra_category_counts(df):
    category_dict = get_product_category_dict(df)
    # TODO: for cakes could create 2 categories for salty and sweet
    for category in ['chicken', 'pork', 'beef', 'ham', 'kebab', 'fish', 'cheese', 'shrimp', 'porridge', 'hamburger', 'pasta', 'salmon', 'cake', 'lamb', 'tofu']:
        food_count = 0
        categoty_count = 0
        for key, value in category_dict.items():
            food_count += value if (category in key.lower()) else 0
            categoty_count += 1 if (category in key.lower()) else 0
        print('Food categories {} and {} foods with {}'.format(
            categoty_count, food_count, category))
    print()


def save_distribution_of_ingredient_count_per_category(df):
    category_dict = get_product_category_dict(df)
    plt.clf()
    plt.bar(range(len(category_dict)), list(
        category_dict.values()), align='center')
    plt.xlabel('Count of categories')
    plt.ylabel('Count of ingredients per category')
    path = 'assets/analytics_of_input_data/ingredient_count_per_category.png'
    plt.savefig(path, bbox_inches='tight')
    print(f'Saved "Count of ingredients per category" chart to {path}\n')


def get_product_category_dict(df):
    cat_dict = {}
    for category in df['category']:
        if not cat_dict.get(category):
            cat_dict[category] = 1
        else:
            cat_dict[category] += 1
    category_dict = {k: v for k, v in sorted(
        cat_dict.items(), key=lambda item: item[1])}
    return category_dict


save_outliers_to_csv(df)
save_energy_difference_distribution(df_no_nan)
print_category_size_distributions(df)
print_extra_category_counts(df)
save_distribution_of_ingredient_count_per_category(df)
