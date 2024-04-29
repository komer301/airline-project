from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql.cursors
import datetime

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='Air Ticket Reservation System',
                       unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        password = request.form.get('password')
        if not user_type or not password:
            return jsonify({'success': False, 'message': 'Missing email or password'}), 400

        if user_type == "Staff":
            username = request.form.get('username')
             # Query the database to check if the user exists
            with conn.cursor() as cursor:
                sql = "SELECT * FROM AirlineStaff WHERE username = %s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
            # User exists and password matches
            # Log the user in here if you are using Flask-Login
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        else:
            email = request.form.get('email')
            with conn.cursor() as cursor:
                sql = "SELECT * FROM Customer WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
            # User exists and password matches
            # Log the user in here if you are using Flask-Login
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template("login.html")

@app.route('/signup', methods=['POST'])
def process_signup():
    email = request.form.get('email')
    password = request.form.get('password')
    user_type = request.form.get('user_type')
    if not email or not password or not user_type:
        return jsonify({'success': False, 'message': 'Missing information'}), 400
 
    if user_type == "Staff":
        username = request.form.get('username')
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Staff WHERE username = %s"
            cursor.execute(sql, (username,))
            existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Staff WHERE email = %s"
            cursor.execute(sql, (email,))
            existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'success': False, 'message': 'Email already exists'}), 409
    else:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Customer WHERE email = %s"
            cursor.execute(sql, (username,))
            existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
 
    # If the user does not exist, insert the new user into the database
    hashed_password = generate_password_hash(password)
    with conn.cursor() as cursor:
        sql = "INSERT INTO Customer (email, password) VALUES (%s, %s)"
        cursor.execute(sql, (email, hashed_password))
        conn.commit()

    return jsonify({'success': True, 'message': 'Signup successful'})

if __name__ == "__main__":
	app.run(debug = True)