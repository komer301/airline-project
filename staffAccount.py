# staffAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request

# Create a Blueprint for staff account management
staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/account')
def dashboard():
    if 'userType' in session and session['userType'] == 'Staff':
        return render_template('staff_account.html')
    return redirect(url_for('home'))


@staff_bp.route('/upcoming-flights')
def profile():
    if 'userType' in session and session['userType'] == 'Staff':
        # Assume getting staff user details logic here
        return render_template('staff_account.html')
    return redirect(url_for('home'))


@staff_bp.route('/create-flight')
def profile():
    if 'userType' in session and session['userType'] == 'Staff':
        # Assume getting staff user details logic here
        return render_template('staff_account.html')
    return redirect(url_for('home'))