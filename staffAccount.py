# staffAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request
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

@staff_bp.route('/create-flight', methods=['GET'])
def create_flight():
    if 'userType' in session and session['userType'] == 'Staff':
        return render_template('staff_account.html')
    return redirect(url_for('home'))
