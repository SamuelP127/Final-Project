from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, DynamicTemplateData
import os
from Words import EXPLICIT_WORDS

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
    # Drop the existing table if it exists and create a new one
    db.drop_all()
    db.create_all()

@app.route('/')
def home():
    reviews = Review.query.filter(
        Review.timestamp >= datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    ).all()
    week_num = datetime.utcnow().isocalendar()[1]

    # Organize reviews by category
    reviews_by_category = {}
    for review in reviews:
        if review.category not in reviews_by_category:
            reviews_by_category[review.category] = []
        reviews_by_category[review.category].append(review)

    return render_template('home.html', reviews=reviews_by_category, week_num=week_num, page='home')

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        reviewer = request.form['reviewer']
        review = request.form['review']
        category = request.form['category']
        anonymous = 'anonymous' in request.form

        if is_explicit(review):
            return "Review contains inappropriate content.", 400

        if anonymous or not reviewer.strip():
            reviewer = "Anonymous"

        new_review = Review(reviewer=reviewer, review=review, category=category)
        db.session.add(new_review)
        db.session.commit()
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
    sg_api_key = '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'
    sg = sendgrid.SendGridAPIClient(api_key=sg_api_key)
    from_email = Email("Samuel.ja.patten@gmail.com")
    to_email = To("Samuel.ja.patten@gmail.com")
    subject = "Weekly BTHS Reviews"
    
    reviews = Review.query.filter(
        Review.timestamp >= datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    ).all()
    
    if not reviews:
        print("No reviews to send")
        return  # No reviews to send
    
    # Convert datetime objects to strings
    dynamic_data = {
        "subject": subject,
        "reviews": [{"reviewer": review.reviewer, "review": review.review, "timestamp": review.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for review in reviews]
    }

    # Use the SendGrid template
    template_id = "d-2cf4fdb5dd6941a795c59cc512faed3d"  # Replace with your actual template ID
    mail = Mail(from_email, to_email)
    mail.dynamic_template_data = dynamic_data
    mail.template_id = template_id
    
    response = sg.client.mail.send.post(request_body=mail.get())
    print(f"SendGrid Response Code: {response.status_code}")
    print(f"SendGrid Response Body: {response.body}")

    if response.status_code == 202:
        # Email sent successfully, now delete the reviews
        for review in reviews:
            db.session.delete(review)
        db.session.commit()
    else:
        print("Failed to send email:", response.status_code, response.body)

def schedule_email():
    scheduler = BackgroundScheduler()
    # Schedule to send email every Sunday at 5 PM
    scheduler.add_job(send_weekly_email, 'cron', day_of_week='sun', hour=17, minute=0)
    scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        init_db()
        schedule_email()
    app.run(debug=True)












#d-2cf4fdb5dd6941a795c59cc512faed3d
#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
