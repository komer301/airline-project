from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql.cursors
from staffAccount import staff_bp  # Import the Blueprint
from userAccount import user_bp
from dotenv import load_dotenv
import os
from datetime import datetime
import re

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
        passport_number = request.form.get('passport_number')
        passport_expiration = request.form.get('passport_expiration')
        passport_country = request.form.get('passport_country')

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
                    address_zip_code,
                    passport_number,
                    passport_expiration,
                    passport_country
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                zipcode,
                passport_number,
                passport_expiration,
                passport_country
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
    departure_location = request.form['departure_airport']  # Modified variable
    arrival_location = request.form['arrival_airport']  # Modified variable
    departure_date = request.form['departure_date_time']
    return_date = request.form.get('return_date_time')

    def get_airports(location):
        sql_airports = """
            SELECT code FROM Airport WHERE city = %s OR code = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(sql_airports, (location, location))
            return [row['code'] for row in cursor.fetchall()]
        
    departure_airports = get_airports(departure_location)
    arrival_airports = get_airports(arrival_location)
    session['departure_airport'] = departure_airports
    session['arrival_airport'] = departure_airports
    session['trip_type'] = trip_type

    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight
            WHERE departure_airport IN %s
            AND arrival_airport IN %s
            AND DATE(departure_date_time) = %s
            AND status != 'Cancelled'
        """
        cursor.execute(sql, (tuple(departure_airports), tuple(arrival_airports), departure_date))
        departure_flights = cursor.fetchall()


        available_flights = []
        for flight in departure_flights:
            is_full, surcharge_applies = is_flight_full(cursor, flight['flight_number'])
            if not is_full:
                flight['price'] = calculate_price(float(flight['base_price']), surcharge_applies)
                flight['departure_date_time'] = flight['departure_date_time'].strftime('%Y-%m-%d %I:%M %p')
                flight['arrival_date_time'] = flight['arrival_date_time'].strftime('%Y-%m-%d %I:%M %p')
                available_flights.append(flight)

    if not available_flights:
        flash('Sorry, no available flights!','warning')
        return(redirect(url_for('home')))
    
    if trip_type == 'one-way':
        return render_template('flight_results.html', flights=available_flights,round_trip=False,goPurchase=True)
    else:
        session['return_date'] = return_date
        return render_template('flight_results.html', flights=departure_flights, round_trip=False, goPurchase=False)


@app.route('/select_return', methods=['POST'])
def select_return():
    selected_flight_key = request.form['selected_flight']
    airline_name, flight_number = selected_flight_key.split('-')
    return_date = session.get('return_date')

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
    def get_airports(location):
        sql_airports = """
            SELECT code FROM Airport WHERE city = %s OR code = %s
        """
        with conn.cursor() as cursor:
            cursor.execute(sql_airports, (location, location))
            return [row['code'] for row in cursor.fetchall()]
        
    departure_airports = get_airports(selected_flight['arrival_airport'])
    arrival_airports = get_airports(selected_flight['departure_airport'])

    with conn.cursor() as cursor:
        sql = """
            SELECT * FROM Flight 
            WHERE departure_airport IN %s
            AND arrival_airport IN %s
            AND DATE(departure_date_time) >= %s
        """
        cursor.execute(sql, (tuple(departure_airports), tuple(arrival_airports), return_date))
        return_flights = cursor.fetchall()

        if not return_flights:
            flash('Sorry, no available flights!', 'warning')
            return redirect(url_for('home'))
        available_flights = []
        for flight in return_flights:
            is_full, surcharge_applies = is_flight_full(cursor, flight['flight_number'])
            if not is_full:
                flight['price'] = calculate_price(flight['base_price'], surcharge_applies)
                flight['departure_date_time'] = flight['departure_date_time'].strftime('%Y-%m-%d %I:%M %p')
                flight['arrival_date_time'] = flight['arrival_date_time'].strftime('%Y-%m-%d %I:%M %p')
                available_flights.append(flight)
            
            
    print(available_flights)
    return render_template('flight_results.html', flights=available_flights, round_trip=True, goPurchase=True)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if request.method == 'POST':
        if 'userType' not in session or session['userType'] != 'Customer':
            flash('You must be signed in as a Customer to purchase a ticket','error')
            return redirect(url_for('home'))
        
        def get_airports(location):
            sql_airports = """
                SELECT code FROM Airport WHERE city = %s OR code = %s
            """
            with conn.cursor() as cursor:
                cursor.execute(sql_airports, (location, location))
                return [row['code'] for row in cursor.fetchall()]
            
        
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
                _, surcharge_applies = is_flight_full(cursor, flight_number)
                selected_flight['price'] = calculate_price(float(selected_flight['base_price']), surcharge_applies)
                selected_flight['departure_date_time'] = selected_flight['departure_date_time'].strftime('%Y-%m-%d %I:%M %p')
                selected_flight['arrival_date_time'] = selected_flight['arrival_date_time'].strftime('%Y-%m-%d %I:%M %p')
            flights = [selected_flight]
            price = float(selected_flight['price'])
            session['price'] = price
            session['flights'] = flights
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
                for flight in flights:
                    _, surcharge_applies = is_flight_full(cursor, flight['flight_number'])
                    flight['price'] = calculate_price(flight['base_price'], surcharge_applies)
                    flight['departure_date_time'] = flight['departure_date_time'].strftime('%Y-%m-%d %I:%M %p')
                    flight['arrival_date_time'] = flight['arrival_date_time'].strftime('%Y-%m-%d %I:%M %p')
            departure_cost = float(flights[0]['price'])
            return_cost = float(flights[1]['price'])
            price = departure_cost + return_cost
            session['price'] = price
            session['flights'] = flights
            print("Flights", flights)
        return render_template('purchase.html', price=price, flights=flights)
    return render_template('purchase.html', price=session['price'], flights=session['flights'])

    
    # Processing payment
@app.route('/complete-purchase',methods=['POST'])
def complete_purchase():
    first_name, last_name, dob = request.form['first_name'], request.form['last_name'], request.form['dob']
    customer_email = request.form['customer_email']
    payment_info = {
        'card_type': request.form['card_type'],
        'card_number': request.form['card_number'],
        'name_on_card': request.form['name_on_card'],
        'expiration_date': request.form['expiration_date'],
        'purchase_date_time': datetime.now()
    }
    if not validate_payment_info(payment_info):
        print("failed")
        return redirect(url_for('purchase'))
    flights = session.get('flights', [])
    if not flights:
            flash('No flights selected for purchase.', 'error')
            return redirect(url_for('home'))
    for flight in flights:
        process_payment(customer_email, flight, payment_info,first_name,last_name,dob)
    
    flash('Payment successful and ticket purchased', 'success')
    return redirect(url_for('home'))


# Check if a flight is full or almost full and calculate price
def is_flight_full(cursor, flight_number):
    sql = """
        SELECT A.num_seats, COUNT(T.id) AS booked_seats
        FROM Airplane A
        JOIN Flight F ON F.airplane_id = A.id
        LEFT JOIN Ticket T ON T.flight_number = F.flight_number
        WHERE F.flight_number = %s
        GROUP BY A.num_seats
    """
    cursor.execute(sql, (flight_number))
    result = cursor.fetchone()
    if not result:
        return False, False  # Flight doesn't exist or no seats booked

    num_seats = result['num_seats']
    booked_seats = result['booked_seats']
    is_full = booked_seats >= num_seats
    surcharge_applies = booked_seats >= 0.8 * num_seats

    return is_full, surcharge_applies

def calculate_price(base_price, surcharge_applies):
    return base_price * 1.25 if surcharge_applies else base_price


def process_payment(customer_email, flight, payment_info,first_name,last_name,dob):
    with conn.cursor() as cursor:
        try:
            year, month = payment_info['expiration_date'].split('-')
            expiration_date = datetime(int(year), int(month), 1).date()
            ticket_sql = """
                INSERT INTO Ticket (customer_email, flight_number, first_name, last_name, date_of_birth, sold_price, payment_info_card_type, payment_info_card_number, payment_info_name_on_card, payment_info_expiration_date, purchase_date_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                ticket_sql,
                (
                    customer_email,
                    flight['flight_number'],
                    first_name,
                    last_name,
                    dob,
                    flight['price'],
                    payment_info['card_type'],
                    payment_info['card_number'],
                    payment_info['name_on_card'],
                    expiration_date,
                    payment_info['purchase_date_time']
                )
            )
            ticket_id = cursor.lastrowid
            
            purchase_sql = """
                INSERT INTO Purchase (ticket_id, customer_email, sold_price, purchase_date_time, card_type, card_number, expiration_date, name_on_card)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                purchase_sql,
                (
                    ticket_id,
                    customer_email,
                    flight['price'],
                    payment_info['purchase_date_time'],
                    payment_info['card_type'],
                    payment_info['card_number'],
                    expiration_date,
                    payment_info['name_on_card']
                )
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f'Error processing payment: {str(e)}')  # More detailed logging
            flash(f'Error processing payment: {str(e)}', 'error')

def validate_payment_info(payment_info):
    card_number = payment_info['card_number']
    if not re.fullmatch(r'\d{16}', card_number):
        flash('Card number must be 16 digits.', 'error')
        return False
    if len((payment_info['name_on_card']).split()) < 2:
        flash('Must have full name on card.', 'error')
        return False
    expiration_date = payment_info['expiration_date']
    try:
        exp_year, exp_month = map(int, expiration_date.split('-'))
        expiration_datetime = datetime(exp_year, exp_month, 1)
        if expiration_datetime < datetime.now():
            flash('Expired card.', 'error')
            return False
    except ValueError:
        flash('Invalid expiration date format.', 'error')
        return False

    name_on_card = payment_info['name_on_card']
    if not name_on_card or len(name_on_card) > 50:
        flash('Invalid name on card.', 'error')
        return False
    return True

@app.route('/logout')
def logout():
    # Clear all data stored in session
    session.clear()
    # Redirect to the landing page (home page in this case)
    return redirect(url_for('login'))

if __name__ == "__main__":
	app.run(debug = True)