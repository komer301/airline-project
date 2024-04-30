# userAccount.py
from flask import Blueprint, render_template, session, redirect, url_for, request

# Create a Blueprint for staff account management
user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/account')
def dashboard():
    if 'userType' in session and session['userType'] == 'Customer':
        return render_template('userAccount.html')
    return redirect(url_for('home'))

@user_bp.route('/profile')
def profile():
    if 'userType' in session and session['userType'] == 'Customer':
        # Assume getting staff user details logic here
        return render_template('signup.html')
    return redirect(url_for('home'))
