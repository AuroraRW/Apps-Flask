from flask import Flask, render_template, g, request
from datetime import datetime
from database import get_db

app = Flask(__name__)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite3'):
        g.sqlite_db.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        date_str = request.form['date']
        # convert string(which format is %Y-%m-%d) to date type
        date = datetime.strptime(date_str, '%Y-%m-%d')
        # convert date type to string(which format is %Y%m%d)
        date_database = datetime.strftime(date, '%Y%m%d')
        db.execute('insert into log_date (entry_date) values (?)', [date_database])
        db.commit()

    cur = db.execute('select log_date.entry_date, sum(food.protein) as protein, '
                     'sum(food.carbohydrates) as carbohydrates, '
                     'sum(food.fat) as fat, sum(food.calories) as calories from log_date '
                     'left join food_date on food_date.log_date_id = log_date.id '
                     'left join food on food.id = food_date.food_id '
                     'group by log_date.id order by log_date.entry_date desc')
    results = cur.fetchall()

    results_final = []
    for item in results:
        single_item = {}
        date = datetime.strptime(str(item['entry_date']), '%Y%m%d')
        single_item['entry_date'] = str(item['entry_date'])
        single_item['date_final'] = datetime.strftime(date, '%B %d, %Y')

        single_item['protein'] = item['protein']
        single_item['carbohydrates'] = item['carbohydrates']
        single_item['fat'] = item['fat']
        single_item['calories'] = item['calories']

        results_final.append(single_item)

    return render_template('home.html', results=results_final)


@app.route('/view/<date>', methods=['GET', 'POST'])
def view(date):
    db = get_db()
    cur = db.execute('select id, entry_date from log_date where entry_date = ?', [date])
    date_result = cur.fetchone()

    # update food_date table if add some food for this day
    if request.method == 'POST':
        db.execute('insert into food_date (food_id, log_date_id) values (?,?)',
                   [request.form['food-select'], date_result['id']])
        db.commit()

    # display date in specific format
    dt = datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    date_final = datetime.strftime(dt, '%B %d, %Y')

    # display food in drop down menu
    cur_food = db.execute('select id, name from food')
    results_food = cur_food.fetchall()

    # display food detail
    cur_log = db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories '
                        'from food join food_date on food.id = food_date.food_id '
                        'join log_date on log_date.id = food_date.log_date_id where log_date.entry_date = ?', [date])
    results_log = cur_log.fetchall()

    # get total
    total = {}
    total['protein'] = 0
    total['carbohydrates'] = 0
    total['fat'] = 0
    total['calories'] = 0

    for result in results_log:
        total['protein'] += result['protein']
        total['carbohydrates'] += result['carbohydrates']
        total['fat'] += result['fat']
        total['calories'] += result['calories']

    return render_template('day.html', entry_date=date_result['entry_date'], date_final=date_final, results_food=results_food, results_log=results_log, total=total)


@app.route('/food', methods=['GET', 'POST'])
def food():
    db = get_db()
    if request.method == 'POST':
        foodName = request.form['foodName']
        protein = int(request.form['protein'])
        carb = int(request.form['carb'])
        fat = int(request.form['fat'])
        calories = protein * 4 + carb * 4 + fat * 9

        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?, ?, ?, ?, ?)', [foodName, protein, carb, fat, calories])
        db.commit()

    cur = db.execute('select name, protein, carbohydrates, fat, calories from food')
    results = cur.fetchall()

    return render_template('add_food.html', results=results)


if __name__ == '__main__':
    app.run()
