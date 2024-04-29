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
    return render_template("login.html")

@app.route('/alogin', methods=['POST'])
def process_login():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing email or password'}), 400

    if email == "test@example.com" and password == "securepassword":
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401



#Configure MySQL
# For MAMP on Mac, add the port or unix_socket AND pwd = "root"

@app.route('/signup', methods=['POST'])
def process_signup():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not email or not password or not confirm_password:
        return jsonify({'success': False, 'message': 'Missing information'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
    
    # Proceed to create the user account...
    return jsonify({'success': True, 'message': 'Signup successful'})

if __name__ == "__main__":
	app.run(debug = True)