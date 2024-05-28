from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime, timedelta

app = Flask("__BTHSThoughts__")
reviews = []

@app.route('/')
@app.route('/home')
def home():
    # Calculate the current week number
    today = datetime.today()
    current_week_num = today.isocalendar()[1]
    
    # Filter reviews for the current week
    current_week_reviews = [
        review for review in reviews
        if datetime.fromisoformat(review['timestamp']).isocalendar()[1] == current_week_num
    ]
    
    return render_template("home.html", reviews=current_week_reviews, week_num=current_week_num, page='home')

@app.route('/about')
def about():
    return render_template("about.html", page='about')

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        reviewer = request.form['reviewer']
        review = request.form['review']
        review_data = {
            'reviewer': reviewer,
            'review': review,
            'timestamp': datetime.now().isoformat()
        }
        reviews.append(review_data)
        return redirect(url_for('home'))
    return render_template("submit_review.html", page='submit_review')

if __name__ == '__main__':
    app.run(debug=True)
