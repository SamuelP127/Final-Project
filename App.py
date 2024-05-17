#app that allows students to rate activities / food / teachers 
#email containing all of these comments are then sent to admin every friday
#What can brooklyn tech do better?

from flask import Flask, request, jsonify, render_template
import smtplib
import json
from datetime import datetime, timedelta
from email.message import EmailMessage
#from apscheduler.schedulers.background import BackgroundScheduler
#log in with School email for a security check

app = Flask("__BTHSThoughts__")
reviews = []

today = datetime.today()
week_num = today.isocalendar()[1]
week = "Week: " + str(week_num)

@app.route('/')
@app.route('/home')
def home():
    return render_template("main.html")

@app.route('/about')
def about():
    return '<h3>This project\'s goal is for BTHS students to share their voice\'s and make positive change!</H3>'

@app.route('/submit_review', methods = ['POST'])
def submit_review():
    review_data = request.json
    review_data['timestamp'] = datetime.now().isoformat()
    reviews.append(review_data)
    return jsonify(status="success", data={"review_submitted": review_data})

def send_email():
    msg = EmailMessage()
    msg['Subject'] = "Students thoughts for week:{week}".format(week)
    msg['From'] = "x@gmail.com"
    msg['To'] = "qholmer@schools.nyc.gov"
    content = ""

if __name__ == '__main__':
    app.run(debug=True)
