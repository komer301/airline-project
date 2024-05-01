from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql.cursors
from staffAccount import staff_bp  # Import the Blueprint
from userAccount import user_bp
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')

app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(user_bp, url_prefix='/user')


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


@app.route('/signup', methods=['GET','POST'])
def process_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Missing email or password', 'error')
            return redirect(url_for('process_signup'))

        with conn.cursor() as cursor:
            sql = "SELECT * FROM Customer WHERE email = %s"
            cursor.execute(sql, (email,))
            existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists', 'error')
            return redirect(url_for('process_signup'))
        
        firstname = request.form.get('first_name')
        lastname = request.form.get('last_name')
        dob = request.form.get('dob')
        aptnumber = request.form.get('apt_number')
        phoneNumber = request.form.get('phone_number')
        street = request.form.get('street_address')
        street_number = request.form.get('building_number')
        state = request.form.get('state')
        city = request.form.get('city')
        zipcode = request.form.get('zip_code')

        hashed_password = generate_password_hash(password)
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO Customer (
                    email, 
                    first_name, 
                    last_name, 
                    date_of_birth, 
                    password, 
                    address_building_number, 
                    address_street_name, 
                    address_apartment_number, 
                    address_city, 
                    address_state, 
                    address_zip_code
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                email, 
                firstname, 
                lastname, 
                dob, 
                hashed_password, 
                street_number, 
                street, 
                aptnumber, 
                city, 
                state, 
                zipcode
            ))
            conn.commit()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO CustomerPhone (
                    email, 
                    phone_number
                ) VALUES (%s, %s)
            """
            cursor.execute(sql, (
                email, 
                phoneNumber
            ))
            conn.commit()

        session['userType'] = 'Customer'
        session['userEmail'] = email
        flash("Signup successful", 'info')
        return redirect(url_for('home'))
    
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return jsonify({'success': False, 'message': 'Missing email or password'}), 400

        with conn.cursor() as cursor:
            sql = "SELECT * FROM Customer WHERE email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['userType'] = 'Customer'
            session['userEmail'] = email
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template("login.html")

@app.route('/stafflogin', methods=['GET', 'POST'])
def staff_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
            return jsonify({'success': False, 'message': 'Missing email or password'}), 400
        
    with conn.cursor() as cursor:
        sql = "SELECT * FROM AirlineStaff WHERE username = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()
    if user and check_password_hash(user['password'], password):
        session['userType'] = 'Staff'
        session['user'] = username
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
 

@app.route('/staff_signup', methods=['GET','POST'])
def process_staff_signup():
    with conn.cursor() as cursor:
            sql = "SELECT * FROM Airline"
            cursor.execute(sql)
            airlines = cursor.fetchall()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')
        firstName = request.form.get('first_name')
        lastName = request.form.get('last_name')
        dateOfBirth = request.form.get('dob')
        airlineName = request.form.get('airline')
        phoneNumber = request.form.get('phone_number')
        missing_fields = []
        if not email:
            missing_fields.append('email')
        if not password:
            missing_fields.append('password')
        if not username:
            missing_fields.append('username')
        if not firstName:
            missing_fields.append('first name')
        if not lastName:
            missing_fields.append('last name')
        if not dateOfBirth:
            missing_fields.append('date of birth')
        if not phoneNumber:
            missing_fields.append("phone number")

        if missing_fields:
            message = "Missing information: " + ", ".join(missing_fields)
            flash(message, 'error')
            return redirect(url_for('process_staff_signup'))


        with conn.cursor() as cursor:
            sql = "SELECT * FROM AirlineStaff WHERE username = %s"
            cursor.execute(sql, (username))
            existing_user = cursor.fetchone()

        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('process_staff_signup'))
        
        with conn.cursor() as cursor:
            sql = "SELECT * FROM StaffEmail WHERE email = %s"
            cursor.execute(sql, (email))
            existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists', 'error')
            return redirect(url_for('process_staff_signup')) 
               
        hashed_password = generate_password_hash(password)
        with conn.cursor() as cursor:
            sql = "INSERT INTO AirlineStaff (username, password, first_name, last_name, date_of_birth, airline_name) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (username, hashed_password, firstName, lastName, dateOfBirth, airlineName))
            conn.commit()
    
        with conn.cursor() as cursor:
            sql = "INSERT INTO StaffEmail (username, email) VALUES (%s, %s)"
            cursor.execute(sql, (username, email))
            conn.commit()

        with conn.cursor() as cursor:
            sql = "INSERT INTO StaffPhone (username, phone_number) VALUES (%s, %s)"
            cursor.execute(sql, (username, phoneNumber))
            conn.commit()
        session['userType'] = 'Staff'
        session['user'] = username
        flash("Signup successful", 'info')
        return redirect(url_for('home'))
    return render_template('staff_signup.html', airlines=airlines)

@app.route('/logout')
def logout():
    # Clear all data stored in session
    session.clear()
    # Redirect to the landing page (home page in this case)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(debug = True)