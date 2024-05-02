# userAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import pymysql.cursors
import phonenumbers
from datetime import datetime, timedelta



# Create a Blueprint for staff account management
user_bp = Blueprint('user', __name__, url_prefix='/user')

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='Air Ticket Reservation System',
                       unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

@user_bp.route('/account', methods=['GET','POST'])
def dashboard():
    # Check if user is logged in and is of type 'Customer'
    if 'userType' in session and session['userType'] == 'Customer':
        email = session.get('userEmail')  # Use consistent session key
        if not email:
            flash("No email found in session.", "error")
            return redirect(url_for('login'))

        # Post method handling for adding a new phone number
        if request.method == 'POST':
            new_phone_number = request.form.get('new_phone_number')
            if new_phone_number:
                try:
                    # Check if phone number already exists for this user
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT * FROM CustomerPhone WHERE email = %s AND phone_number = %s", (email, new_phone_number))
                        existing_phone = cursor.fetchone()
                        if existing_phone:
                            flash("Phone number already exists.", "error")
                        elif len(new_phone_number) != 10:
                            flash("Phone number format incorrect", "error")
                        else:
                            # Add phone number to database
                            add_phone_number_to_db(email,new_phone_number)
                            flash("Phone number added successfully", "success")
                except Exception as e:
                    flash(str(e), "error")
            return redirect(url_for('user.dashboard'))

        # Get user's first name and phone numbers from the database
        user_first_name, phone_numbers = None, []
        try:
            with conn.cursor() as cursor:
                # Query to get user's first name
                cursor.execute("SELECT first_name FROM Customer WHERE email = %s", (email,))
                result = cursor.fetchone()
                if result:
                    user_first_name = result['first_name']
                
                # Function to get phone numbers, handling it within the same DB connection
                phone_numbers = get_user_phone_numbers(email)
        except Exception as e:
            flash("Database error: " + str(e), "error")
            return redirect(url_for('login'))

        if user_first_name:  # Check if user information was successfully retrieved
            return render_template('userAccount.html', user_first_name=user_first_name, phone_numbers=phone_numbers)
        else:
            flash("User not found.", "error")
            return redirect(url_for('login'))
    else:
        flash("You are not authorized to access this page.", "error")
        return redirect(url_for('home'))


def add_phone_number_to_db(email, phone_number):
    with conn.cursor() as cursor:
        # Assuming you have a 'PhoneNumbers' table with 'email' and 'phone_number' columns
        sql = "INSERT INTO CustomerPhone (email, phone_number) VALUES (%s, %s)"
        cursor.execute(sql, (email, phone_number))
        conn.commit()

def get_user_phone_numbers(email):
    with conn.cursor() as cursor:
        sql = "SELECT phone_number FROM CustomerPhone WHERE email = %s"
        cursor.execute(sql, (email,))
        # Fetch all results
        results = cursor.fetchall()
        # Extract phone numbers from the query results
        phone_numbers = [format_phone_number(result['phone_number']) for result in results]
        return phone_numbers

@user_bp.route('/delete_phone_number/<phone_number>', methods=['POST'])
def delete_phone_number(phone_number):
    if 'userType' in session and session['userType'] == 'Customer':
        try:
            with conn.cursor() as cursor:
                # Assuming you have a table 'PhoneNumbers' with a column 'number' and 'email'
                sql = "DELETE FROM CustomerPhone WHERE phone_number = %s AND email = %s"
                cursor.execute(sql, (unformat_phone_number(phone_number), session['userEmail']))
                conn.commit()
            flash('Phone number removed successfully', 'success')
        except Exception as e:
            flash(str(e), 'error')
    else:
        flash('You are not authorized to perform this action.', 'error')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/profile')
def profile():
    if 'userType' in session and session['userType'] == 'Customer':
        # Assume getting staff user details logic here
        return render_template('signup.html')
    return redirect(url_for('home'))

@user_bp.route('/my-flights', methods=['GET', 'POST'])
def my_flights():
    if 'userType' not in session or session['userType'] != 'Customer':
        flash("Unauthorized access.", "error")
        return redirect(url_for('home'))

    flights=[]
    customer_email = session['userEmail']

    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        departure_airport = request.form.get('departure_airport')
        arrival_airport = request.form.get('arrival_airport')
        flights = query_flights(customer_email, from_date, to_date, departure_airport, arrival_airport)
    else:
        flights = query_flights(customer_email)
    return render_template('my_flights.html', flights=flights)

def query_flights(customer_email, from_date=None, to_date=None, departure_airport=None, arrival_airport=None):
    # Default date range for the next 30 days if no dates are specified
    if not from_date:
        from_date = datetime.now().strftime('%Y-%m-%d')
    
    query = """
        SELECT t.*
        FROM ticket t
        JOIN purchase p ON t.customer_email = p.customer_email
        WHERE p.customer_email = %s
        AND f.departure_date > %s
    """

    # Prepare the parameters list for the query
    params = [customer_email, from_date]

    # Filter by departure and arrival airports if provided
    if to_date:
        query += " AND f.arrival_airport <= %s"
        params.append(to_date)
    if departure_airport:
        query += " AND f.departure_airport = %s"
        params.append(departure_airport)
    if arrival_airport:
        query += " AND f.arrival_airport = %s"
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
    
         
@user_bp.route('/my-spending', methods=['GET', 'POST'])
def my_spending():
    if 'userType' not in session or session['userType'] != 'Customer':
        flash("Unauthorized access.", "error")
        return redirect(url_for('home'))
    
    customer_email = session['userEmail']
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        yearly_spending, monthly_spending = get_sum(customer_email, from_date, to_date)
    else:
        yearly_spending, monthly_spending = get_sum(customer_email)
    return render_template('something.html', yearly_spending=yearly_spending, monthly_spending=monthly_spending)

def get_sum(customer_email, from_date=None, to_date=None):
    try:
        with conn.cursor() as cursor:
            if from_date and to_date:
                query1 = """
                SELECT SUM(p.sold_price) AS total_spent_past_year
                FROM purchase p
                WHERE p.customer_email = %s
                AND p.purchase_date_time >= %s
                AND p.purchase_date_time <= %s;
                """
                query2 = """
                SELECT YEAR(p.purchase_date_time) AS year,
                    MONTH(p.purchase_date_time) AS month,
                    SUM(p.sold_price) AS total_spent
                FROM purchase p
                WHERE p.customer_email = %s
                AND p.purchase_date_time >= %s
                AND p.purchase_date_time <= %s
                GROUP BY YEAR(p.purchase_date_time), MONTH(p.purchase_date_time)
                ORDER BY year DESC, month DESC;
                """
                cursor.execute(query1, (customer_email, from_date, to_date))
                total_yearly = cursor.fetchall()
                cursor.execute(query2, (customer_email, from_date, to_date))
                total_monthly = cursor.fetchall()
            else:
                query1 = """
                SELECT SUM(p.sold_price) AS total_spent_past_year
                FROM purchase p
                WHERE p.customer_email = %s
                AND p.purchase_date_time >= DATE_SUB(NOW(), INTERVAL 1 YEAR);
                """
                query2 = """
                SELECT YEAR(p.purchase_date_time) AS year,
                    MONTH(p.purchase_date_time) AS month,
                    SUM(p.sold_price) AS total_spent
                FROM purchase p
                WHERE p.customer_email = %s
                AND p.purchase_date_time >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                GROUP BY YEAR(p.purchase_date_time), MONTH(p.purchase_date_time)
                ORDER BY year DESC, month DESC;
                """
                cursor.execute(query1, (customer_email))
                total_yearly = cursor.fetchall()
                cursor.execute(query2, (customer_email))
                total_monthly = cursor.fetchall()
            
            return total_yearly, total_monthly
        
    except Exception as e:
            flash(str(e), 'error')

@user_bp.route('/my-reviews', methods=['GET', 'POST'])
def my_reviews():
    if 'userType' not in session or session['userType'] != 'Customer':
        flash("Unauthorized access.", "error")
        return redirect(url_for('home'))
    
    customer_email = session['userEmail']
    
    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id')
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        
        # Check if the ticket corresponds to a flight that has already been taken
        check_query = """
        SELECT 1
        FROM ticket t
        JOIN took tk ON t.flight_id = tk.flight_id
        JOIN flight f ON t.flight_id = f.flight_id
        WHERE t.id = %s AND tk.email = %s AND f.arrival_date_time <= CURRENT_TIMESTAMP
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(check_query, (ticket_id, customer_email))
                result = cursor.fetchone()
                
                if result:
                    # If the ticket corresponds to a taken flight, update the rating and comment
                    update_query = """
                    UPDATE took
                    SET rating = %s, comment = %s
                    WHERE email = %s AND flight_id = (
                        SELECT flight_id FROM ticket WHERE id = %s
                    )
                    """
                    
                    cursor.execute(update_query, (rating, comment, customer_email, ticket_id))
                    conn.commit()
                    flash("Review submitted successfully.", "success")
                else:
                    flash("This ticket does not correspond to a flight you've taken.", "error")
                
        except Exception as e:
            flash(str(e), 'error')
        return redirect(url_for('user.my_reviews'))

    else:
        select_query = """
        SELECT rating, comment
        FROM took
        WHERE email = %s AND rating IS NOT NULL AND comment IS NOT NULL
        """
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(select_query, (customer_email,))
                reviews = cursor.fetchall()
                
                return render_template('my_reviews.html', reviews=reviews)
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('home'))




# Helper functions
def format_phone_number(raw_number):
    try:
        phone_number = phonenumbers.parse(raw_number, "US") 
        return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.phonenumberutil.NumberParseException:
        return raw_number 

def unformat_phone_number(formatted_number):
    try:
        phone_number = phonenumbers.parse(formatted_number, None)
        return str(phone_number.national_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return None  
