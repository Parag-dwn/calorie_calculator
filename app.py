from flask import Flask,Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
import os
from models import Food, Log
from datetime import datetime 
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from PIL import Image


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret-key'
upload_folder = os.path.join('static', 'uploads')
predict_folder = os.path.join('static', 'predicted')
app.config['UPLOAD'] = upload_folder
app.config['PREDICT']=predict_folder
db.init_app(app)
with app.app_context():
    db.create_all()



if __name__ == '__main__':
    app.run(debug=True,port=8001)





@app.route('/')
def index():
    logs = Log.query.order_by(Log.date.desc()).all()

    log_dates = []

    for log in logs:
        proteins = 0
        carbs = 0
        fats = 0
        calories = 0

        for food in log.foods:
            proteins += food.proteins
            carbs += food.carbs 
            fats += food.fats
            calories += food.calories

        log_dates.append({
            'log_date' : log,
            'proteins' : proteins,
            'carbs' : carbs,
            'fats' : fats,
            'calories' : calories
        })
    return render_template('index.html', log_dates=log_dates)

@app.route('/upload',methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['img']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD'], filename))
        img = os.path.join(app.config['UPLOAD'], filename)
        data=detection(img,filename)
        predict=os.path.join(app.config['PREDICT'], filename)
        content=''
        #print(filename)
        return render_template('upload.html',img=predict,data=data)
    name='Dal'
    #item=df[df['Name ']==name].values[0]
    #data=c(name)
    return render_template('upload.html')

def detection(image_path,filename):
    model = YOLO('D:/downloads/calorietracker-master/calorietracker-master/calorietracker/best (1).pt')
    results= model.predict(image_path)
    for r in results:
        im_array = r.plot()  # plot a BGR numpy array of predictions
    im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
    #im.show()  # show image
    im.save(predict_folder+'/' +filename)    
    result=results[0]
    classes=model.names
    Names=[]
    Calories=[]
    protein=[]
    fat=[]
    carbs=[]
    quantity=[]
    df=pd.read_excel('D:\downloads\calorietracker-master\calorietracker-master\Food item calories .xlsx')
    vals={'n':0}
    for r in results:
        for i in (r.boxes.cls):
            name=classes[int(i)]
            item=df[df['Name ']==name].values[0]
            vals['n']+=1
            Names.append(item[0])
            Calories.append(item[1])
            protein.append(item[2])
            fat.append(item[3])
            carbs.append(item[4])
    data={
        'Name':Names,
        'calories':Calories,
        'protein':protein,
        'fat':fat,
        'carbs':carbs,
        'vals':vals
        
    }
    return data

def add_meal(item):
    meal_name=item[0].lower()
    foods = Food.query.all()
    counter = db.session.query(Food).filter(Food.name == food_name).count()
    if counter >=1:
        flash('This Food Already Exist!', 'info')
        return redirect(url_for('upload'))
    else:
        new_food = Food(
            name=meal_name,
            proteins=item[2], 
            carbs=item[3], 
            fats=item[4]
        )
        db.session.add(new_food)
 
    db.session.commit()
def meal_log(food_name):
    
    try:
        log = Log.query.get_or_404(log_id)
        selected_food=food_name.lower()
        food = Food.query.get(int(selected_food))
        
        log.foods.append(food)
        db.session.commit()

        return redirect(url_for('view', log_id=log_id))
    
    except:
        flash('Only One Type of Food per day Allowed!', 'info')
        return redirect(url_for('view', log_id=log_id))
    

@app.route('/create_log', methods=['POST'])
def create_log():
    date = request.form.get('date')

    log = Log(date=datetime.strptime(date, '%Y-%m-%d'))

    db.session.add(log)
    db.session.commit()

    return redirect(url_for('view', log_id=log.id))

@app.route('/delete_log/<int:log_id>')
def delete_log(log_id):
    log = Log.query.get_or_404(log_id)
    print(log)
    db.session.delete(log)
    db.session.commit()
    
    return redirect(url_for('index', log_id=log.id))
    

    

@app.route('/add')
def add():
    foods = Food.query.all()
    return render_template('add.html', foods=foods, food=None)

@app.route('/add', methods=['POST'])
def add_post():
    food_name = request.form.get('food-name').lower()
    proteins = request.form.get('protein').lower()
    carbs = request.form.get('carbohydrates').lower()
    fats = request.form.get('fat').lower()
    
    food_id = request.form.get('food-id')
    print(food_id)
    
    foods = Food.query.all()
    counter = db.session.query(Food).filter(Food.name == food_name).count()
     
   

    if food_id:
        food = Food.query.get_or_404(food_id)
        food.name = food_name
        food.proteins = proteins
        food.carbs = carbs
        food.fats = fats
        
    elif counter >=1:
        flash('This Food Already Exist!', 'info')
        return redirect(url_for('add'))
        
    else:
        new_food = Food(
            name=food_name,
            proteins=proteins, 
            carbs=carbs, 
            fats=fats
        )
    
        db.session.add(new_food)

    db.session.commit()

    return redirect(url_for('add'))

@app.route('/delete_food/<int:food_id>')
def delete_food(food_id):
    food = Food.query.get_or_404(food_id)
    db.session.delete(food)
    db.session.commit()

    return redirect(url_for('add'))

@app.route('/edit_food/<int:food_id>')
def edit_food(food_id):
    food = Food.query.get_or_404(food_id)
    foods = Food.query.all()

    return render_template('add.html', food=food, foods=foods)
    
@app.route('/view/<int:log_id>')
def view(log_id):
    log = Log.query.get_or_404(log_id)
    
    foods = Food.query.all()
    

    totals = {
        'protein' : 0,
        'carbs' : 0,
        'fat' : 0,
        'calories' : 0
    }

    for food in log.foods:
        totals['protein'] += food.proteins
        totals['carbs'] += food.carbs
        totals['fat'] += food.fats 
        totals['calories'] += food.calories

    return render_template('view.html', foods=foods, log=log, totals=totals)

@app.route('/add_food_to_log/<int:log_id>', methods=['POST'])
def add_food_to_log(log_id):
    try:
        log = Log.query.get_or_404(log_id)
        
        selected_food = request.form.get('food-select').lower()
        food = Food.query.get(int(selected_food))
            
        log.foods.append(food)
        db.session.commit()


        return redirect(url_for('view', log_id=log_id))
    
    except:
        flash('Only One Type of Food per day Allowed!', 'info')
        return redirect(url_for('view', log_id=log_id))




  
@app.route('/remove_food_from_log/<int:log_id>/<int:food_id>')
def remove_food_from_log(log_id, food_id):
    log = Log.query.get(log_id)
    food = Food.query.get(food_id)

    log.foods.remove(food)
    db.session.commit()
    return redirect(url_for('view', log_id=log_id))



