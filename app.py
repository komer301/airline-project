from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql.cursors
from staffAccount import staff_bp  # Import the Blueprint
from userAccount import user_bp
from dotenv import load_dotenv
import os
from datetime import datetime

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

@app.route('/status', methods=['POST'])
def check_status():
    airline = request.form.get('airline')
    flight_number = request.form.get('flight_number')
    departure_date = request.form.get('date')

    if not airline or not flight_number or not departure_date:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('home'))
    
    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight 
            WHERE airline_name = %s 
            AND flight_number = %s 
            AND DATE(departure_date_time) = %s
        """
        cursor.execute(sql, (airline, flight_number, departure_date))
        flight = cursor.fetchone()

        if not flight:
            flash("Flight not found or no status available.", 'error')
            return redirect(url_for('home'))
        
        departure_dt = flight['departure_date_time']
        arrival_dt = flight['arrival_date_time']
        
        flight['departure_time'] = departure_dt.strftime("%I:%M %p")
        flight['arrival_time'] = arrival_dt.strftime("%I:%M %p")
        
    return render_template('flight_status.html', flight=flight)

@app.route('/search', methods=['POST'])
def search_flights():
    trip_type = request.form['trip_type']
    departure_airport = request.form['departure_airport']
    arrival_airport = request.form['arrival_airport']
    departure_date = request.form['departure_date_time']
    return_date = request.form.get('return_date_time')

    session['departure_airport'] = departure_airport
    session['arrival_airport'] = arrival_airport
    session['trip_type'] = trip_type

    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight 
            WHERE departure_airport = %s 
            AND arrival_airport = %s 
            AND DATE(departure_date_time) = %s
            AND status != 'Cancelled'
        """
        cursor.execute(sql, (departure_airport, arrival_airport, departure_date))
        departure_flights = cursor.fetchall()

    if not departure_flights:
        flash('Sorry, no available flights!','warning')
        return(redirect(url_for('home')))
    
    if trip_type == 'one-way':
        return render_template('flight_results.html', flights=departure_flights,round_trip=False,goPurchase=True)
    else:
        session['return_date'] = return_date
        return render_template('flight_results.html', flights=departure_flights, round_trip=False, goPurchase=False)


@app.route('/select_return', methods=['POST'])
def select_return():
    selected_flight_key = request.form['selected_flight']
    airline_name, flight_number = selected_flight_key.split('-')
    return_date = session.get('return_date')

    # try:
    #     return_date_parsed = datetime.strptime(session['return_date'], '%Y-%m-%d')
    # except (ValueError, TypeError):
    #     flash('Invalid return date format', 'error')
    #     return redirect(url_for('home'))
    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight 
            WHERE airline_name = %s 
            AND flight_number = %s 
        """
        cursor.execute(sql, (airline_name, flight_number))
        selected_flight = cursor.fetchone()
        print("Selected flight",selected_flight)
    
    session['selected_departure_flight'] = selected_flight

    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight 
            WHERE departure_airport = %s 
            AND arrival_airport = %s 
            AND DATE(departure_date_time) >= %s
        """
        cursor.execute(sql, (selected_flight['arrival_airport'], selected_flight['departure_airport'], session['return_date']))
        return_flights = cursor.fetchall()
    if not return_flights:
        flash('Sorry, no available flights!','warning')
        return redirect(url_for('home'))

    return render_template('flight_results.html', flights=return_flights, round_trip=True, goPurchase=True)



@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        if 'userType' not in session or session['userType'] != 'Customer':
            flash('You must be signed in as a Customer to purchase a ticket','error')
            return redirect(url_for('home'))
        if session.get('trip_type') == 'one-way':
            selected_flight_key = request.form['selected_flight']
            airline_name, flight_number = selected_flight_key.split('-')
            
            with conn.cursor() as cursor:
                sql = """
                    SELECT * FROM Flight 
                    WHERE airline_name = %s 
                    AND flight_number = %s
                """
                cursor.execute(sql, (airline_name, flight_number))
                selected_flight = cursor.fetchone()
            
            flights = [selected_flight]
            price = float(selected_flight['base_price'])
        else:
            selected_return_flight_key = request.form['selected_flight']
            airline_name, flight_number = selected_return_flight_key.split('-')
            
            with conn.cursor() as cursor:
                sql = """
                    SELECT * FROM Flight 
                    WHERE airline_name = %s 
                    AND flight_number = %s
                """
                cursor.execute(sql, (airline_name, flight_number))
                selected_return_flight = cursor.fetchone()
            
            flights = [session['selected_departure_flight'], selected_return_flight]
            departure_cost = float(session['selected_departure_flight']['base_price'])
            return_cost = float(selected_return_flight['base_price'])
            price = departure_cost + return_cost
            session['flights'] = flights
        return render_template('purchase.html', price=price, flights=flights)
    
    # Processing payment
@app.route('/complete-purchase',methods=['POST'])
def complete_purchase():
    customer_email = request.form['customer_email']
    payment_info = {
        'card_type': request.form['card_type'],
        'card_number': request.form['card_number'],
        'name_on_card': request.form['name_on_card'],
        'expiration_date': request.form['expiration_date'],
        'purchase_date_time': datetime.now()
    }
    flights = session.get('flights', [])
    
    for flight in flights:
        process_payment(customer_email, flight, payment_info)
    
    flash('Purchase successful', 'success')
    return redirect(url_for('home'))


def process_payment(customer_email, flight, payment_info):
    with conn.cursor() as cursor:
        try:
            print("First check point")
            year, month = payment_info['expiration_date'].split('-')
            expiration_date = datetime(int(year), int(month), 1).date()
            ticket_sql = """
                INSERT INTO Ticket (customer_email, flight_number, sold_price, payment_info_card_type, payment_info_card_number, payment_info_name_on_card, payment_info_expiration_date, purchase_date_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                ticket_sql,
                (
                    customer_email,
                    flight['flight_number'],
                    flight['base_price'],
                    payment_info['card_type'],
                    payment_info['card_number'],
                    payment_info['name_on_card'],
                    expiration_date,
                    payment_info['purchase_date_time']
                )
            )
            print("Second check point")
            print(customer_email,flight,payment_info)
            
            ticket_id = cursor.lastrowid
            print("ticketID",ticket_id)
            
            purchase_sql = """
                INSERT INTO Purchase (ticket_id, customer_email, sold_price, purchase_date_time, card_type, card_number, expiration_date, name_on_card)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                purchase_sql,
                (
                    ticket_id,
                    customer_email,
                    flight['base_price'],
                    payment_info['purchase_date_time'],
                    payment_info['card_type'],
                    payment_info['card_number'],
                    expiration_date,
                    payment_info['name_on_card']
                )
            )
            conn.commit()
            flash('Payment successful and ticket purchased', 'success')

        except Exception as e:
            conn.rollback()
            print(f'Error processing payment: {str(e)}')  # More detailed logging
            flash(f'Error processing payment: {str(e)}', 'error')



def calculate_price(flight):
    return flight['base_price']

@app.route('/logout')
def logout():
    # Clear all data stored in session
    session.clear()
    # Redirect to the landing page (home page in this case)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(debug = True)