# staffAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import pymysql.cursors
from datetime import datetime, timedelta
import phonenumbers


# Create a Blueprint for staff account management
staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='Air Ticket Reservation System2',
                       unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@staff_bp.route('/account', methods=['GET'])
def dashboard():
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
        airline_name = request.form.get('airline_name')
        departure_airport = request.form.get('departure_airport')
        arrival_airport = request.form.get('arrival_airport')
        departure_date_time = validate_and_correct_date(request.form.get('departure_date_time'))
        arrival_date_time = validate_and_correct_date(request.form.get('arrival_date_time'))
        base_price = request.form.get('base_price')
        status = request.form.get('status')

        try:
            airline_name = get_airline_name_from_staff(session['user'])
            with conn.cursor() as cursor:
                if entity_exists(cursor, "Flight", "flight_number", flight_number):
                    flash('Flight Number already exists.', 'error')
                elif not entity_exists(cursor, "Airline", "name", airline_name):
                    flash('Airline does not exist.', 'error')
                elif not entity_exists(cursor, "Airplane", "id", airplane_id):
                    flash('Airplane does not exist.', 'error')
                elif not entity_exists(cursor, "Airport", "code", departure_airport):
                    flash('Departure airport does not exist.', 'error')
                elif not entity_exists(cursor, "Airport", "code", arrival_airport):
                    flash("Arrival airport does not exist", "error")
                elif not airport_types_compatible(cursor,departure_airport,arrival_airport):
                    flash("Airport types are not the same", "error")
                elif arrival_date_time <= departure_date_time:
                    flash("Arrival time must be later than departure time.", "error")
                    return redirect(url_for('staff.create_flight'))
                else:
                    cursor.execute("SELECT * FROM Maintenance WHERE airplane_id = %s AND (%s BETWEEN start_date_time AND end_date_time OR %s BETWEEN start_date_time AND end_date_time)",
                               (airplane_id, departure_date_time, arrival_date_time))
                    if cursor.fetchone():
                        flash("Airplane is scheduled for maintenance during the flight time.", "error")
                        return redirect(url_for('staff.create_flight'))
                    print(departure_date_time,arrival_date_time)
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
    airplanes = [] 
    try:
            airline_name = get_airline_name_from_staff(session['user'])
            airplanes = find_airplanes(airline_name)
    except Exception as e:
            flash(f"Failed to load airplanes: {str(e)}", 'error')
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
                
                # Insert new airplane
                sql = """
                    INSERT INTO Airplane (airline_name, id, num_seats, manufacturer, model_num, manufacturing_date, age)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (airline_name, airplane_id, num_seats, manufacturer, model_num, manufacturing_date, age))
                conn.commit()
                flash('Airplane successfully created.', 'success')
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('staff.create_airplane'))

    return render_template('create_airplane.html', company=airline_name, airplanes=airplanes)

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
                        INSERT INTO Airport (code, name, city, country, airport_type, num_of_terminals)
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
                        UPDATE Flight
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

@staff_bp.route('/schedule-maintenance', methods=['GET','POST'])
def schedule_maintenance():
    if 'userType' in session and session['userType'] == 'Staff':
        if request.method == 'POST':
            airplane_id = request.form.get('airplane_id')
            start_date_time = validate_and_correct_date(request.form.get('start_date_time'))
            end_date_time = validate_and_correct_date(request.form.get('end_date_time'))

            airline_name = get_airline_name_from_staff(session['user'])

            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM Airplane WHERE id = %s AND airline_name = %s", (airplane_id, airline_name))
                airplane = cursor.fetchone()
                if not airplane:
                    flash('Airplane ID or Airline does not exist.', 'error')
                    return redirect(url_for('staff.schedule_maintenance'))

                # Check maintenance scheduling conflicts or logical errors
                if end_date_time <= start_date_time:
                    flash('End date must be later than start date.', 'error')
                    return redirect(url_for('staff.schedule_maintenance'))

                # Insert maintenance record
                try:
                    sql = """
                    INSERT INTO Maintenance (airline_name, airplane_id, start_date_time, end_date_time)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql, (airline_name, airplane_id, start_date_time, end_date_time))
                    conn.commit()
                    flash('Maintenance scheduled successfully.', 'success')
                except Exception as e:
                    conn.rollback()
                    flash(str(e), 'error')
            
            return redirect(url_for('staff.schedule_maintenance'))
        return render_template('schedule_maintenance.html')



    return redirect(url_for('home'))

@staff_bp.route('/upcoming-flights', methods=['GET', 'POST'])
def upcoming_flights():
    if 'userType' not in session or session['userType'] != 'Staff':
        flash("Unauthorized access.", "error")
        return redirect(url_for('home'))

    airline_name = get_airline_name_from_staff(session['user'])
    flights=[]

    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        departure_airport = request.form.get('departure_airport')
        arrival_airport = request.form.get('arrival_airport')
        flights = query_flights(airline_name, from_date, to_date, departure_airport, arrival_airport)
    else:
        flights = query_flights(airline_name)
    for flight in flights:
        flight['departure_date_time'] = flight['departure_date_time'].strftime('%Y-%m-%d %I:%M %p')
        flight['arrival_date_time'] = flight['arrival_date_time'].strftime('%Y-%m-%d %I:%M %p')
    return render_template('upcoming_flights.html', flights=flights)

@staff_bp.route('/flight/<flight_number>/passengers', methods=['GET'])
def flight_passengers(flight_number):
    if 'userType' not in session or session['userType'] != 'Staff':
        flash("Unauthorized access.", "error")
        return redirect(url_for('home'))

    airline_name = get_airline_name_from_staff(session['user'])
    passengers = []

    with conn.cursor() as cursor:
        sql = """
            SELECT t.id, t.customer_email, t.first_name, t.last_name, t.date_of_birth, t.sold_price, t.purchase_date_time
            FROM Ticket t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s AND f.flight_number = %s
        """
        cursor.execute(sql, (airline_name, flight_number))
        passengers = cursor.fetchall()

    return render_template('flight_passengers.html', passengers=passengers, flight_number=flight_number)


@staff_bp.route('/account-settings', methods=['GET', 'POST'])
def staff_settings():
    if 'userType' not in session or session['userType'] != 'Staff':
        flash("You need to log in as a staff member to access staff settings", "error")
        return redirect(url_for('login'))

    username = session['user']
    with conn.cursor() as cursor:
        sql = "SELECT first_name FROM AirlineStaff WHERE username = %s"
        cursor.execute(sql,username)
        first_name = (cursor.fetchone())['first_name']

    if request.method == 'POST':
        new_email = request.form.get('new_email')
        new_phone_number = request.form.get('new_phone_number')

        try:
            if new_email:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO StaffEmail (username, email) VALUES (%s, %s)"
                    cursor.execute(sql, (username, new_email))
                    conn.commit()
                flash("Email added successfully", "success")

            if new_phone_number:
                try:
                    # Check if phone number already exists for this user
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM StaffPhone WHERE username = %s AND phone_number = %s", (username, new_phone_number))
                        existing_phone = cursor.fetchone()
                        if existing_phone:
                            flash("Phone number already exists.", "error")
                        elif len(new_phone_number) != 10:
                            flash("Phone number format incorrect", "error")
                        else:
                            # Add phone number to database
                            add_phone_number_to_db(username,new_phone_number)
                            flash("Phone number added successfully", "success")
                except Exception as e:
                    flash(str(e), "error")

        except Exception as e:
            flash(str(e), 'error')
        
        return redirect(url_for('staff.staff_settings'))

    emails = get_user_emails(username)
    phone_numbers = get_user_phone_numbers(username)

    return render_template(
        'staff_account_settings.html',
        emails=emails,
        phone_numbers=phone_numbers, staff_first_name=first_name
    )

@staff_bp.route('/frequent-customer', methods=['GET'])
def frequent_customer():
    username = session.get('user')
    airline_name = get_airline_name_from_staff(username)
    
    if not airline_name:
        flash("Airline name not found for this staff member.", "error")
        return redirect(url_for('staff.dashboard'))
    
    one_year_ago = datetime.now() - timedelta(days=365)
    frequent_customer_data = None
    taken_flights = []

    with conn.cursor() as c:
        # Query to find the most frequent customer in the last year
        frequent_customer_query = """
            SELECT t.customer_email, COUNT(*) AS num_flights
            FROM Ticket t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s AND t.purchase_date_time > %s
            GROUP BY t.customer_email
            ORDER BY num_flights DESC
            LIMIT 1
        """
        c.execute(frequent_customer_query, (airline_name, one_year_ago))
        frequent_customer_data = c.fetchone()
        
        if frequent_customer_data:
            customer_email = frequent_customer_data['customer_email']
            
            # Query to get all flights taken by the customer in the airline
            flights_query = """
                SELECT f.flight_number, f.departure_date_time, f.arrival_date_time,
                       f.departure_airport, f.arrival_airport, t.sold_price
                FROM Ticket t
                JOIN Flight f ON t.flight_number = f.flight_number
                WHERE t.customer_email = %s AND f.airline_name = %s
                ORDER BY f.departure_date_time
            """
        c.execute(flights_query, (customer_email, airline_name))
        taken_flights = c.fetchall()
        
        customer_name = """
                SELECT CONCAT(first_name, ' ' ,last_name) AS full_name
                FROM Customer 
                WHERE email = %s
            """
        c.execute(customer_name, (customer_email))
        customer_name = c.fetchall()
        customer_name = customer_name[0]['full_name']

    return render_template('frequent_customer.html', customer_name=customer_name,frequent_customer_data=frequent_customer_data, taken_flights=taken_flights)

@staff_bp.route('/view-earnings', methods=['GET', 'POST'])
def view_earnings():
    username = session.get('user')
    airline_name = get_airline_name_from_staff(username)

    if not airline_name:
        flash("Airline name not found for this staff member.", "error")
        return redirect(url_for('staff.dashboard'))
    
    with conn.cursor() as c:
        # Start of last month and last year
        last_month_start = datetime.now().replace(day=1) - timedelta(days=1)
        last_month_start = last_month_start.replace(day=1)

        last_year_start = datetime.now().replace(month=1, day=1) - timedelta(days=1)
        last_year_start = last_year_start.replace(month=1, day=1)
        
        # Query for last month earnings
        query_last_month = """
            SELECT SUM(t.sold_price) AS total_revenue_last_month
            FROM Ticket t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s AND t.purchase_date_time >= %s
        """
        c.execute(query_last_month, (airline_name, last_month_start))
        last_month_row = c.fetchone()
        last_month = float(last_month_row['total_revenue_last_month']) if last_month_row and last_month_row['total_revenue_last_month'] else 0.00
        
        # Query for last year earnings
        query_last_year = """
            SELECT SUM(t.sold_price) AS total_revenue_last_year
            FROM Ticket t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s AND t.purchase_date_time >= %s
        """
        c.execute(query_last_year, (airline_name, last_year_start))
        last_year_row = c.fetchone()
        last_year = float(last_year_row['total_revenue_last_year']) if last_year_row and last_year_row['total_revenue_last_year'] else 0.00
    selected_month = None
    tickets = []

    if request.method == 'POST':
        # Extract and format the selected month
        month_str = request.form['month']
        selected_month = datetime.strptime(month_str, "%Y-%m").strftime("%B %Y")
        
        start_date = datetime.strptime(month_str, "%Y-%m")
        end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1)
                    if start_date.month != 12
                    else start_date.replace(year=start_date.year + 1, month=1, day=1))
        
        with conn.cursor() as c:
            ticket_query = """
                SELECT t.id, t.customer_email, t.flight_number, t.sold_price, t.purchase_date_time
                FROM Ticket t
                JOIN Flight f ON t.flight_number = f.flight_number
                WHERE f.airline_name = %s AND t.purchase_date_time >= %s AND t.purchase_date_time < %s
            """
            c.execute(ticket_query, (airline_name, start_date, end_date))
            tickets = c.fetchall()
    else:
        start_date = datetime.now().replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        selected_month = start_date.strftime("%B %Y")
    
    end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1)
                if start_date.month != 12
                else start_date.replace(year=start_date.year + 1, month=1, day=1))
    with conn.cursor() as c: 
        ticket_query = """
            SELECT t.id, t.customer_email, t.flight_number, t.sold_price, t.purchase_date_time
            FROM Ticket t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s AND t.purchase_date_time >= %s AND t.purchase_date_time < %s
        """
        c.execute(ticket_query, (airline_name, start_date, end_date))
        tickets = c.fetchall()

        for ticket in tickets:
            # Format purchase_date_time to "Month Day Year Hour:Minute AM/PM"
            purchase_date_time = ticket['purchase_date_time']
            ticket['purchase_date_time'] = purchase_date_time.strftime("%B %d %Y %I:%M %p")
            
    return render_template('view_earnings.html', last_month=last_month, last_year=last_year,
                           selected_month=selected_month, tickets=tickets)


@staff_bp.route('/view-ratings', methods=['GET'])
def view_ratings():
    username = session.get('user')
    airline_name = get_airline_name_from_staff(username)

    if not airline_name:
        flash("Airline name not found for this staff member.", "error")
        return redirect(url_for('staff.dashboard'))

    with conn.cursor() as c:
        ratings_query = """
            SELECT t.flight_number, f.departure_airport, f.arrival_airport, 
                   AVG(t.rating) AS avg_rating, 
                   GROUP_CONCAT(t.comment ORDER BY t.comment) AS comments
            FROM Took t
            JOIN Flight f ON t.flight_number = f.flight_number
            WHERE f.airline_name = %s
            GROUP BY t.flight_number, f.departure_airport, f.arrival_airport
            ORDER BY t.flight_number
        """
        c.execute(ratings_query, (airline_name,))
        flight_ratings = c.fetchall()

    return render_template('view_ratings.html', flight_ratings=flight_ratings)


@staff_bp.route('/delete_phone_number/<phone_number>', methods=['POST'])
def delete_phone_number(phone_number):
    if 'userType' in session and session['userType'] == 'Staff':
        try:
            with conn.cursor() as cursor:
                # Assuming you have a table 'PhoneNumbers' with a column 'number' and 'email'
                sql = "DELETE FROM StaffPhone WHERE phone_number = %s AND username = %s"
                cursor.execute(sql, (unformat_phone_number(phone_number), session['user']))
                conn.commit()
            flash('Phone number removed successfully', 'success')
        except Exception as e:
            flash(str(e), 'error')
    else:
        flash('You are not authorized to perform this action.', 'error')
    return redirect(url_for('staff.staff_settings'))

@staff_bp.route('/delete_email/<email>', methods=['POST'])
def delete_email(email):
    if 'userType' in session and session['userType'] == 'Staff':
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM StaffEmail WHERE email = %s AND username = %s"
                cursor.execute(sql, (email, session['user']))
                conn.commit()
            flash('Email removed successfully', 'success')
        except Exception as e:
            flash(str(e), 'error')
    else:
        flash('You are not authorized to perform this action.', 'error')
    return redirect(url_for('staff.staff_settings'))

def get_user_phone_numbers(username):
    with conn.cursor() as cursor:
        sql = "SELECT phone_number FROM StaffPhone WHERE username = %s"
        cursor.execute(sql, (username))
        # Fetch all results
        results = cursor.fetchall()
        # Extract phone numbers from the query results
        phone_numbers = [format_phone_number(result['phone_number']) for result in results]
        return phone_numbers
    
def get_user_emails(username):
    with conn.cursor() as cursor:
        sql = "SELECT email FROM StaffEmail WHERE username = %s"
        cursor.execute(sql, (username))
        # Fetch all results
        results = cursor.fetchall()
        # Extract phone numbers from the query results
        phone_numbers = [format_phone_number(result['email']) for result in results]
        return phone_numbers
    
def add_phone_number_to_db(username, phone_number):
    with conn.cursor() as cursor:
        sql = "INSERT INTO StaffPhone (username, phone_number) VALUES (%s, %s)"
        cursor.execute(sql, (username, phone_number))
        conn.commit()

def format_phone_number(raw_number):
    try:
        phone_number = phonenumbers.parse(raw_number, "US")  # Assume 'US' as the region; adjust as necessary
        return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.phonenumberutil.NumberParseException:
        return raw_number  # Return the raw number if parsing fails

def unformat_phone_number(formatted_number):
    try:
        phone_number = phonenumbers.parse(formatted_number, None)
        # Extracts the national number part of the phone number, which omits country code and formatting
        return str(phone_number.national_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return None  # Return None or handle the error as needed if the number can't be parsed


def query_flights(airline_name, from_date=None, to_date=None, departure_airport=None, arrival_airport=None):
    # Default date range for the next 30 days if no dates are specified
    if not from_date:
        from_date = datetime.now().strftime('%Y-%m-%d')
    if not to_date:
        to_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    # Start building the query with the condition to exclude cancelled flights
    query = """
        SELECT * FROM Flight
        WHERE airline_name = %s
        AND departure_date_time BETWEEN %s AND %s
        AND status != 'Cancelled'
    """

    # Prepare the parameters list for the query
    params = [airline_name, from_date, to_date]

    # Filter by departure and arrival airports if provided
    if departure_airport:
        query += " AND departure_airport = %s"
        params.append(departure_airport)
    if arrival_airport:
        query += " AND arrival_airport = %s"
        params.append(arrival_airport)
    
    # Execute the query
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query, params)
            flights = cursor.fetchall()
            return flights
    except Exception as e:
        print("Failed to query flights:", e)
        return []


def get_airline_name_from_staff(username):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT airline_name FROM AirlineStaff WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result:
                return result['airline_name']
            else:
                return None
    except Exception as e:
        print(f"Error retrieving airline name: {e}")
        return None



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
    cursor.execute("SELECT airport_type FROM Airport WHERE code = %s", (departure))
    departure_type = cursor.fetchone()
    cursor.execute("SELECT airport_type FROM Airport WHERE code = %s", (arrival))
    arrival_type = cursor.fetchone()

    if departure_type and arrival_type:
        if departure_type['airport_type'] == 'Both' or arrival_type['airport_type'] == 'Both':
            return True
        # Example logic: disallowing international flights from domestic only airports
        return departure_type['airport_type'] == arrival_type['airport_type']
    return False  # In case of missing data

def validate_and_correct_date(date_time_str):
    parts = date_time_str.split('T')
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else '00:00'

    year, month, day = date_part.split('-')

    # Check if the year is longer than 4 characters and try to correct it
    if len(year) > 4:
        year = year[:4]  # Take the first four digits assuming extra digit at the start

    # Reconstruct the date-time string with corrected year
    corrected_date_time_str = f"{year}-{month}-{day}T{time_part}"
    try:
        return datetime.strptime(corrected_date_time_str, "%Y-%m-%dT%H:%M")
    except ValueError as e:
        flash(f"Invalid date format or value: {e}", 'error')
        return None
    
def find_airplanes(company):
    with conn.cursor() as cursor:
        sql = "SELECT * FROM Airplane WHERE airline_name = %s"
        cursor.execute(sql, (company))
        return cursor.fetchall()
    # return a list of the airplanes