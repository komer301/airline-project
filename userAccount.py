# userAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
import pymysql.cursors
import phonenumbers




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
