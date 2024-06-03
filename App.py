from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, DynamicTemplateData
import os
from Words import EXPLICIT_WORDS
import logging

#logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

Filter_words = EXPLICIT_WORDS

def is_explicit(content):
    for word in EXPLICIT_WORDS:
        if word in content.lower():
            return True
    return False

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer = db.Column(db.String(100), nullable=False)
    review = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def init_db():
    logging.debug("Initializing the database")
    db.drop_all()
    db.create_all()

@app.route('/')
def home():
    logging.debug("Fetching reviews for the current week")
    # Calculate the start of the current week
    today = datetime.utcnow().date()
    start_of_week = datetime(today.year, today.month, today.day) - timedelta(days=today.weekday())
    reviews = Review.query.filter(Review.timestamp >= start_of_week).all()
    week_num = datetime.utcnow().isocalendar()[1]

    reviews_by_category = {}
    for review in reviews:
        if review.category not in reviews_by_category:
            reviews_by_category[review.category] = []
        reviews_by_category[review.category].append(review)

    logging.debug(f"Reviews fetched: {reviews_by_category}")
    return render_template('home.html', reviews=reviews_by_category, week_num=week_num, page='home')

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        reviewer = request.form['reviewer']
        review = request.form['review']
        category = request.form['category']
        anonymous = 'anonymous' in request.form

        if is_explicit(review):
            logging.warning("Review contains inappropriate content")
            return "Review contains inappropriate content.", 400

        if anonymous or not reviewer.strip():
            reviewer = "Anonymous"

        new_review = Review(reviewer=reviewer, review=review, category=category)
        logging.debug(f"New review: {new_review}")
        db.session.add(new_review)
        db.session.commit()
        logging.debug("Review submitted successfully")

        # Debug: print all reviews in the database
        all_reviews = Review.query.all()
        logging.debug(f"All reviews in the database: {all_reviews}")

        return redirect(url_for('home'))
    return render_template('submit_review.html', page='submit_review')

@app.route('/about')
def about():
    return render_template('about.html', page='about')

@app.route('/send_email')
def send_email():
    send_weekly_email()
    return redirect(url_for('home'))

def send_weekly_email():
    sg_api_key = ''
    sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)
    from_email = Email("Samuel.ja.patten@gmail.com")
    to_email = To("Samuel.ja.patten@gmail.com")
    subject = "Weekly BTHS Reviews"
    
    today = datetime.utcnow().date()
    start_of_week = datetime(today.year, today.month, today.day) - timedelta(days=today.weekday())
    reviews = Review.query.filter(Review.timestamp >= start_of_week).all()
    
    if not reviews:
        logging.info("No reviews to send")
        return
    
    dynamic_data = {
        "subject": subject,
        "reviews": [{"reviewer": review.reviewer, "review": review.review, "timestamp": review.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for review in reviews]
    }

    template_id = "d-2cf4fdb5dd6941a795c59cc512faed3d"
    mail = Mail(from_email, to_email)
    mail.dynamic_template_data = dynamic_data
    mail.template_id = template_id
    
    response = sg.client.mail.send.post(request_body=mail.get())
    logging.debug(f"SendGrid Response Code: {response.status_code}")
    logging.debug(f"SendGrid Response Body: {response.body}")

    if response.status_code == 202:
        for review in reviews:
            db.session.delete(review)
        db.session.commit()
    else:
        logging.error(f"Failed to send email: {response.status_code}, {response.body}")

def schedule_email():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_weekly_email, 'cron', day_of_week='sun', hour=17, minute=0)
    scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        # This stops the database from opening and closing everytime program is started
        # init_db()
        schedule_email()
    app.run(debug=True)

#d-2cf4fdb5dd6941a795c59cc512faed3d
