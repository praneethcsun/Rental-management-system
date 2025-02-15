from flask import Flask, request, render_template, redirect, url_for, session
from datetime import timedelta, date
import os
import re
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Hash password function
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

# Set session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Database connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='user_management',
            user='root',
            password='GpkTHEboss@007'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        phone = request.form['phone']

        if password != confirm_password:
            return "Passwords do not match!"

        phone_regex = r'^\+?1?\d{9,15}$'
        if not re.match(phone_regex, phone):
            return "Invalid phone number format! Please enter a valid phone number."

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            return "Invalid email format! Please enter a valid email."

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return "Username already exists."
                
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return "Email already exists."
                
                cursor.execute("SELECT phone FROM users WHERE phone = %s", (phone,))
                if cursor.fetchone():
                    return "Phone number already exists."

                hashed_password = hash_password(password)
                query = """INSERT INTO users (username, password, firstName, lastName, email, phone)
                           VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (username, hashed_password, firstName, lastName, email, phone))
                connection.commit()
                session['username'] = username
                return redirect(url_for('dashboard'))
            finally:
                cursor.close()
                connection.close()

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = "SELECT password, firstName, lastName, email, phone FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                result = cursor.fetchone()

                if result:
                    stored_password = result[0]
                    firstName, lastName, email, phone = result[1], result[2], result[3], result[4]
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        session['username'] = username
                        return redirect(url_for('dashboard'))
                    else:
                        return "Invalid password!"
                else:
                    return "Username does not exist!"
            finally:
                cursor.close()
                connection.close()

    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT firstName, lastName, email, phone FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if result:
                firstName, lastName, email, phone = result[0], result[1], result[2], result[3]
                return render_template('dashboard.html', username=username, firstName=firstName, lastName=lastName, email=email, phone=phone)
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('login'))

# Add rental
@app.route('/add_rental', methods=['GET', 'POST'])
def add_rental():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['username']
        title = request.form['title']
        description = request.form['description']
        feature = request.form['feature']
        price = request.form['price']
        post_date = date.today()

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM rental_units WHERE user_id = %s AND post_date = %s", (user_id, post_date))
                rental_count = cursor.fetchone()[0]
                if rental_count >= 2:
                    return "You can only post 2 rental units per day."

                query = """INSERT INTO rental_units (user_id, title, description, feature, price, post_date)
                           VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (user_id, title, description, feature, price, post_date))
                connection.commit()
                return redirect(url_for('dashboard'))
            finally:
                cursor.close()
                connection.close()

    return render_template('add_rental.html')

# Search rentals
@app.route('/search_rentals', methods=['GET', 'POST'])
def search_rentals():
    if request.method == 'POST':
        feature = request.form['feature']
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = "SELECT rental_id, title, description, feature, price FROM rental_units WHERE feature LIKE %s"
                cursor.execute(query, ('%' + feature + '%',))
                rentals = cursor.fetchall()
                return render_template('rental_results.html', rentals=rentals)
            finally:
                cursor.close()
                connection.close()
    return render_template('search_rentals.html')

# Add review
@app.route('/add_review/<int:rental_id>', methods=['GET', 'POST'])
def add_review(rental_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['username']

    if request.method == 'POST':
        rating = request.form['rating']
        description = request.form['description']
        review_date = date.today()

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT user_id FROM rental_units WHERE rental_id = %s", (rental_id,))
                owner = cursor.fetchone()
                if owner and owner[0] == user_id:
                    return "You cannot review your own rental."

                cursor.execute("SELECT COUNT(*) FROM reviews WHERE user_id = %s AND review_date = %s", (user_id, review_date))
                review_count = cursor.fetchone()[0]
                if review_count >= 3:
                    return "You can only submit 3 reviews per day."

                cursor.execute("SELECT * FROM reviews WHERE user_id = %s AND rental_id = %s", (user_id, rental_id))
                if cursor.fetchone():
                    return "You have already reviewed this rental."

                query = """INSERT INTO reviews (user_id, rental_id, rating, description, review_date)
                           VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(query, (user_id, rental_id, rating, description, review_date))
                connection.commit()
                return redirect(url_for('dashboard'))
            finally:
                cursor.close()
                connection.close()

    return render_template('add_review.html', rental_id=rental_id)

# Change password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "New passwords do not match!"

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                username = session.get('username')
                query = "SELECT password FROM users WHERE username = %s"
                cursor.execute(query, (username,))
                result = cursor.fetchone()

                if result and bcrypt.checkpw(current_password.encode('utf-8'), result[0].encode('utf-8')):
                    hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    update_query = "UPDATE users SET password = %s WHERE username = %s"
                    cursor.execute(update_query, (hashed_new_password, username))
                    connection.commit()
                    return "Password updated successfully!"
                else:
                    return "Current password is incorrect."
            finally:
                cursor.close()
                connection.close()
        return "Unable to connect to the database."
    return render_template('change_password.html')

# Phase 3 Routes
@app.route('/most_expensive_rentals')
def most_expensive_rentals():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "SELECT feature, MAX(price) AS max_price FROM rental_units GROUP BY feature;"
            cursor.execute(query)
            results = cursor.fetchall()
            return render_template('most_expensive_rentals.html', rentals=results)
        finally:
            cursor.close()
            connection.close()

@app.route('/search_users_by_features', methods=['GET', 'POST'])
def search_users_by_features():
    if request.method == 'POST':
        feature1 = request.form['feature1']
        feature2 = request.form['feature2']
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                SELECT r1.user_id
                FROM rental_units r1
                JOIN rental_units r2 
                ON r1.user_id = r2.user_id AND r1.post_date = r2.post_date AND r1.rental_id != r2.rental_id
                WHERE r1.feature LIKE %s AND r2.feature LIKE %s
                GROUP BY r1.user_id;
                """
                cursor.execute(query, (f"%{feature1}%", f"%{feature2}%"))
                results = cursor.fetchall()
                return render_template('search_users_by_features.html', users=results)
            finally:
                cursor.close()
                connection.close()
    return render_template('search_users_by_features.html')

@app.route('/user_good_rentals', methods=['GET', 'POST'])
def user_good_rentals():
    if request.method == 'POST':
        user_id = request.form['user_id']
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                SELECT r.*
                FROM rental_units r
                JOIN reviews rv ON r.rental_id = rv.rental_id
                WHERE r.user_id = %s
                GROUP BY r.rental_id
                HAVING COUNT(CASE WHEN rv.rating NOT IN ('Excellent', 'Good') THEN 1 END) = 0;
                """
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                return render_template('user_good_rentals.html', rentals=results)
            finally:
                cursor.close()
                connection.close()
    return render_template('user_good_rentals.html')

# Users with Only Poor Reviews
@app.route('/users_with_only_poor_reviews')
def users_with_only_poor_reviews():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT r.user_id, r.title
            FROM rental_units r
            JOIN reviews rv ON r.rental_id = rv.rental_id
            WHERE rv.rating = 'Poor'
            AND NOT EXISTS (
                SELECT 1
                FROM reviews rv2
                WHERE rv2.rental_id = rv.rental_id AND rv2.rating != 'Poor'
            );
            """
            cursor.execute(query)
            rentals = cursor.fetchall()
            return render_template('users_with_only_poor_reviews.html', rentals=rentals)
        finally:
            cursor.close()
            connection.close()


 
# Users Whose Rentals Never Received Poor Reviews
@app.route('/users_with_no_poor_reviews')
def users_with_no_poor_reviews():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = """
            SELECT r.user_id, r.title
            FROM rental_units r
            WHERE NOT EXISTS (
                SELECT 1
                FROM reviews rv
                WHERE rv.rental_id = r.rental_id AND rv.rating = 'Poor'
            );
            """
            cursor.execute(query)
            rentals = cursor.fetchall()
            return render_template('users_with_no_poor_reviews.html', rentals=rentals)
        finally:
            cursor.close()
            connection.close()

            
@app.route('/top_posters_by_date', methods=['GET', 'POST'])
def top_posters_by_date():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        post_date = request.form['post_date']
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """
                SELECT user_id, COUNT(*) AS rental_count
                FROM rental_units
                WHERE post_date = %s
                GROUP BY user_id
                HAVING rental_count = (
                    SELECT MAX(rental_count) 
                    FROM (
                        SELECT COUNT(*) AS rental_count 
                        FROM rental_units 
                        WHERE post_date = %s
                        GROUP BY user_id
                    ) subquery
                );
                """
                cursor.execute(query, (post_date, post_date))
                results = cursor.fetchall()
                return render_template('top_posters_by_date.html', date=post_date, users=results)
            finally:
                cursor.close()
                connection.close()
    return render_template('top_posters_by_date.html')


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
