from flask import Flask, request, redirect, url_for
from flask import render_template
import pandas as pd
import data_import
import algorithm
import glob
import time
import random
import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)

LOCAL = DEBUG = True  # False is only for production

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.form.get('password'):
        return redirect(url_for('meal_plan', days=request.form['days']))
    return render_template('index.html', wrong_password=True)


def calculate(days, allergy, low_salt):
    df = data_import.get_data()
    df = data_import.clean_data(df)

    previous_day = None
    used_meals = None
    start = time.time()
    for day_count in range(days):
        day_name = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][day_count % 7]
        day_name = str(day_count) + ''
        day = algorithm.DailyMealPlan(
            df, 
            limits={'allergies': [allergy], 'low_salt':low_salt},
            day=day_name,
            prev_meal_plan=previous_day, 
            used_meals=used_meals)
        message = ' '.join(['-'*20, 'Meal Plan:', day_name.upper(), '-'*20])
        logging.info(message)
        meal_plan = day.get_optimal_meal_plan()
        logging.info(meal_plan)

        used_meals = pd.concat([used_meals, meal_plan])
        day.save_meal_plan_to_csv()
        day.save_total_nutrients_to_csv()
        logging.info(day.get_total_nutrients())
        previous_day = day

    end = time.time()
    message = ' '.join(['-'*20, 'Running time:', str(end - start), '-'*20])
    logging.info(message)
    return 


@app.route('/upadate-meal-plan', methods=['GET', 'POST'])
def update_meal_plan():
    if not request.form.get('days'):
        return redirect(url_for('meal_plan'))
    days = request.form.get('days')
    days = int(days)
    allergy = 'lactose' if request.form.get('allergy') else ''
    low_salt = True if request.form.get('low_salt') else False
    min_sugar = True if request.form.get('min_sugar') else False
    new_meal_plan = True if request.form.get('new_meal_plan') else False
    if new_meal_plan and LOCAL:
        calculate(days, allergy, low_salt)
    elif new_meal_plan and not LOCAL:
        meal_plans, nutrients = get_nutrients_and_meal_plans(
            days, allergy=allergy, low_salt=low_salt, min_sugar=min_sugar, new_meal_plan=False)
        return render_template('meal_plan.html', meal_plans=meal_plans, nutrients=nutrients, days=days, server=True)

    meal_plans, nutrients = get_nutrients_and_meal_plans(
        days, allergy=allergy, low_salt=low_salt, min_sugar=min_sugar, new_meal_plan=new_meal_plan)
    return render_template('meal_plan.html', meal_plans=meal_plans, nutrients=nutrients, days=days)


@app.route('/meal-plan')
@app.route('/meal-plan/<days>', methods=['GET', 'POST'])
def meal_plan(days=7):
    days = int(days)
    meal_plans, nutrients = get_nutrients_and_meal_plans(days)
    return render_template('meal_plan.html', meal_plans=meal_plans, nutrients=nutrients, days=days)

def get_nutrients_and_meal_plans(days, allergy=None, low_salt=None, min_sugar=True, new_meal_plan=False):
    def convert_info_to_list_of_dicts(info_dict, min_sugar, days):
        if min_sugar:
            sorted_tuples = sorted(info_dict.items())
        else:
            sorted_tuples = sorted(info_dict.items())
            # TODO: Commenting this because then there might be same food category on successive days
            # Have to figure another way to shuffle the meal plans (algorithm level solution)
            # sorted_tuples = sorted(info_dict.items(), key=lambda x: random.random())

        info_list = []
        count = 1
        for i, value in sorted_tuples:
            info_list.append(value)
            if count == days:
                break
            count += 1
        return info_list
    
    # Meal Plans
    meal_plans_dict = {}
    if new_meal_plan:
        if low_salt:
            path = "daily_meal_plans/new_low_salt/*meal_plan*.csv"
        else:
            path = "daily_meal_plans/new/*meal_plan.csv"
    else:
        if low_salt:
            path = "daily_meal_plans/pre_low_salt/*meal_plan_low_salt.csv"
        else:
            path = "daily_meal_plans/pre/*meal_plan.csv"
    i = 1
    for fname in glob.glob(path):
        df = pd.read_csv(fname, sep=",")
        df = df.append(df.sum(numeric_only=True), ignore_index=True)
        df.loc[df.index[-1], 'name'] = 'Total'
        if allergy and df['lactose'].iloc[-1] != 0:
            continue # TODO: this causes a slight change of same food category on successive days
                     # This can be fixed in the algorithm level
        df['salt'] = df['salt'].div(1000) # mg -> g
        key = int(fname.split('/')[-1].split('_')[0])
        meal_plans_dict[key] = df.round(1).to_dict('list')
        # meal_plans_dict[df['sugar'].iloc[-1]] = df.round(1).to_dict('list')
        i += 1
    meal_plans = convert_info_to_list_of_dicts(meal_plans_dict, min_sugar, days)

    # Nutrients
    nutrients_dict = {}
    if new_meal_plan:
        if low_salt:
            path = "daily_meal_plans/new_low_salt/*nutrients*.csv"
        else:
            path = "daily_meal_plans/new/*nutrients.csv"
    else:
        if low_salt:
            path = "daily_meal_plans/pre_low_salt/*nutrients_low_salt.csv"
        else:
            path = "daily_meal_plans/pre/*nutrients.csv"
    i = 1
    for fname in glob.glob(path):
        df = pd.read_csv(fname, sep=",")
        df = df.set_index('Unnamed: 0')
        df = df.T
        if allergy and df['lactose'].iloc[-1] != 0:
            continue # TODO: this causes a slight change of same food category on successive days
                     # This can be fixed in the algorithm level
        key = int(fname.split('/')[-1].split('_')[0])
        nutrients_dict[key] = df.round(1).to_dict('list')
        # nutrients_dict[df['sugar'].iloc[-1]] = df.round(1).to_dict('list')
        i += 1
    nutrients = convert_info_to_list_of_dicts(nutrients_dict, min_sugar, days)
    return meal_plans, nutrients

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.form.get('feedback'):
        return render_template('feedback.html', feedback=True)
    return render_template('feedback.html')


@app.route('/calculate')
def test():
    return render_template('index.html', test='Test ID is 123123123')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=DEBUG)
