import pandas as pd
import data_import
import algorithm
import time

df = data_import.get_data()
df = data_import.clean_data(df)

previous_day = None
used_meals = None
start = time.time()
days = 7
for day_count in range(days):
    day_name = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][day_count % 7]
    day_name = '_'.join([str(day_count), day_name])
    day = algorithm.DailyMealPlan(
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
