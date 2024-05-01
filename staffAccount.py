# staffAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import pymysql.cursors

# Create a Blueprint for staff account management
staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='Air Ticket Reservation System',
                       unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@staff_bp.route('/account', methods=['GET'])
def dashboard():
    if 'userType' in session and session['userType'] == 'Staff':
        return render_template('staff_account.html')
    return redirect(url_for('home'))

@staff_bp.route('/upcoming-flights', methods=['GET'])
def upcoming_flights():
    if 'userType' in session and session['userType'] == 'Staff':
        return render_template('staff_account.html')
    return redirect(url_for('home'))

@staff_bp.route('/create-flight', methods=['GET', 'POST'])
def create_flight():
    if 'userType' not in session or session['userType'] != 'Staff':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Extract form data
        airplane_id = request.form.get('airplane_id')
        flight_number = request.form.get('flight_number')
        departure_airport = request.form.get('departure_airport')
        arrival_airport = request.form.get('arrival_airport')
        departure_date_time = request.form.get('departure_date_time')
        arrival_date_time = request.form.get('arrival_date_time')
        base_price = request.form.get('base_price')
        status = request.form.get('status')
        # Perform database checks and insert new flight
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT airline_name FROM AirlineStaff WHERE username = %s", (session['user']))
                airline_name = (cursor.fetchone())['airline_name']
                if entity_exists(cursor, "Flight", "flight_number", flight_number):
                    flash('Flight Number already exists.', 'error')
                elif not entity_exists(cursor, "Airline", "name", airline_name):
                    flash('Airline does not exist.', 'error')
                elif not entity_exists(cursor, "Airplane", "id", airplane_id):
                    flash('Airplane does not exist.', 'error')
                elif not entity_exists(cursor, "Airport", "name", departure_airport):
                    flash('Departure airport does not exist.', 'error')
                elif not entity_exists(cursor, "Airport", "name", arrival_airport):
                    flash("Arrival airport does not exist", "error")
                elif not airport_types_compatible(cursor,departure_airport,arrival_airport):
                    flash("Airport types are not the same", "error")
                else:
                    insert_flight(cursor, flight_number, airline_name, departure_date_time, departure_airport, arrival_airport, arrival_date_time, base_price, airplane_id, status)
                    flash('Flight successfully created.', 'success')
            conn.commit()
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('staff.create_flight'))

    return render_template('create_flight.html')

@staff_bp.route('/create-airplane', methods=['GET', 'POST'])
def create_airplane():
    if 'userType' not in session or session['userType'] != 'Staff':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Extract form data
        airplane_id = request.form.get('airplane_id')
        num_seats = request.form.get('num_seats')
        manufacturer = request.form.get('manufacturer')
        model_num = request.form.get('model_num')
        manufacturing_date = request.form.get('manufacturing_date')
        age = request.form.get('age')

        # Perform database checks and insert new flight
        try:
            with conn.cursor() as cursor:
                # Check if the airplane ID already exists
                if entity_exists(cursor, "Airplane", "id", airplane_id):
                    flash('Airplane ID already exists.', 'error')
                    return redirect(url_for('staff.create_airplane'))
                cursor.execute("SELECT airline_name FROM AirlineStaff WHERE username = %s", (session['user']))
                airline_name = (cursor.fetchone())['airline_name']
                # Insert new airplane
                sql = """
                    INSERT INTO Airplane (airline_name, id, num_seats, manufacturer, model_num, manufacturing_date, age)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (airplane_id, airline_name, num_seats, manufacturer, model_num, manufacturing_date, age))
                conn.commit()
                flash('Airplane successfully created.', 'success')
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('staff.create_flight'))

    return render_template('create_airplane.html')

@staff_bp.route('/create-airport', methods=['GET', 'POST'])
def create_airport():
    if 'userType' in session and session['userType'] == 'Staff':
        if request.method == 'POST':
            code = request.form.get('code')
            name = request.form.get('name')
            city = request.form.get('city')
            country = request.form.get('country')
            airport_type = request.form.get('airport_type')
            num_of_terminals = request.form.get('num_of_terminals')

            if len(code) > 4:
                flash("Airport code incorrect","error")
                return redirect(url_for("staff.create_airport"))
            # Check for existing airport by code or name
            with conn.cursor() as cursor:
                if entity_exists(cursor, "Airport", "code", code) or entity_exists(cursor, "Airport", "name", name):
                    flash('Airport code or name already exists.', 'error')
                    return redirect(url_for('staff.create_airport'))

                # Insert the new airport if validations are passed
                try:
                    cursor.execute("""
                        INSERT INTO Airports (code, name, city, country, airport_type, num_of_terminals)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (code, name, city, country, airport_type, int(num_of_terminals)))
                    conn.commit()
                    flash('Airport successfully created.', 'success')
                except Exception as e:
                    conn.rollback()
                    flash(str(e), 'error')
            
            return redirect(url_for('staff.create_airport'))

        return render_template('create_airport.html')
    else:
        flash('You are not authorized to view this page.', 'error')
        return redirect(url_for('home'))

@staff_bp.route('/change-flight-status', methods=['GET','POST'])
def change_flight_status():
    if 'userType' in session and session['userType'] == 'Staff' and 'user' in session:
        if request.method == 'POST':
            flight_number = request.form.get('flight_number')
            new_status = request.form.get('status')
            username = session['user']

            with conn.cursor() as cursor:
                # Verify if the flight belongs to the airline staff is part of
                cursor.execute("""
                    SELECT f.flight_number FROM Flight f
                    JOIN AirlineStaff s ON f.airline_name = s.airline_name
                    WHERE s.username = %s AND f.flight_number = %s
                """, (username, flight_number))
                flight = cursor.fetchone()

                if flight:
                    # Update the flight status
                    cursor.execute("""
                        UPDATE Flights
                        SET status = %s
                        WHERE flight_number = %s
                    """, (new_status, flight_number))
                    conn.commit()
                    flash('Flight status updated successfully.', 'success')
                else:
                    flash('No such flight found for your airline.', 'error')
            return redirect(url_for('staff.change_flight_status'))
        return render_template('change_flight_status.html')
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('home'))



# helper functions
def entity_exists(cursor, table, column, value):
    """Check if an entity exists in the database."""
    query = f"SELECT 1 FROM {table} WHERE {column} = %s"
    cursor.execute(query, (value,))
    return cursor.fetchone() is not None

def insert_flight(cursor, flight_number, airline_name, departure_date_time, departure_airport, arrival_airport, arrival_date_time, base_price, airplane_id, status):
    """Insert a new flight into the database."""
    sql = """
        INSERT INTO Flight (flight_number, airline_name, departure_date_time, departure_airport, arrival_airport, arrival_date_time, base_price, airplane_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (flight_number, airline_name, departure_date_time, departure_airport, arrival_airport, arrival_date_time, base_price, airplane_id, status))

def airport_types_compatible(cursor, departure, arrival):
    """Check if departure and arrival airports are compatible in terms of their types."""
    cursor.execute("SELECT airport_type FROM Airport WHERE name = %s", (departure))
    departure_type = cursor.fetchone()
    cursor.execute("SELECT airport_type FROM Airport WHERE name = %s", (arrival))
    arrival_type = cursor.fetchone()

    if departure_type and arrival_type:
        if departure_type['airport_type'] == 'Both' or arrival_type['airport_type'] == 'Both':
            return True
        # Example logic: disallowing international flights from domestic only airports
        return departure_type['airport_type'] == arrival_type['airport_type']
    return False  # In case of missing data