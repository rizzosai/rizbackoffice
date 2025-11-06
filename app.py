
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import json
from datetime import datetime, timedelta
from functools import wraps
# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'replace-this-with-a-secure-key')

# Admin credentials from environment
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password123')

# File paths
CUSTOMERS_FILE = 'customers.json'
PACKAGES_FILE = 'packages.json'
COMMISSIONS_FILE = 'commissions.json'
QUEUE_FILE = 'queue.json'

# Helper functions
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_package_info(level):
    packages = load_json(PACKAGES_FILE)
    return packages.get(str(level), packages.get("1"))

def get_accessible_guides(level):
    # All guides are now available to everyone
    all_guides = [
        {"id": 1, "title": "Domain Mastery 101", "description": "How to choose, register & optimize domains for maximum profit", "level": 1},
        {"id": 2, "title": "AI-Powered Landing Pages", "description": "Create high-converting landing pages with AI", "level": 1},
        {"id": 3, "title": "Affiliate Marketing Secrets", "description": "Unlock the secrets to successful affiliate marketing", "level": 2},
        {"id": 4, "title": "Advanced Traffic Strategies", "description": "Drive massive traffic to your offers", "level": 3},
        {"id": 5, "title": "Empire Building", "description": "Scale your business to the next level", "level": 4}
    ]
    # No guides are locked
    return [{**g, "locked": False} for g in all_guides]

def add_to_queue(email, referrer=None):
    queue_data = load_json(QUEUE_FILE)
    if 'queue' not in queue_data:
        queue_data['queue'] = []
    # Prevent duplicate entries
    if any(person['email'] == email for person in queue_data['queue']):
        return
    entry = {'email': email, 'joined': datetime.utcnow().isoformat()}
    if referrer:
        entry['referrer'] = referrer
    queue_data['queue'].append(entry)
    save_json(QUEUE_FILE, queue_data)

def assign_commission(referrer_email, amount):
    commissions = load_json(COMMISSIONS_FILE)
    if referrer_email not in commissions:
        commissions[referrer_email] = {'total_earned': 0, 'payments': []}
    commissions[referrer_email]['total_earned'] += amount
    commissions[referrer_email]['payments'].append({
        'amount': amount,
        'date': datetime.utcnow().isoformat()
    })
    save_json(COMMISSIONS_FILE, commissions)

def is_admin():
    return session.get('customer_email') == ADMIN_USERNAME

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ROUTES
@app.route('/')
def home():
    if 'customer_email' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        # Debug print statements
        print("ADMIN_USERNAME from env:", ADMIN_USERNAME)
        print("ADMIN_PASSWORD from env:", ADMIN_PASSWORD)
        print("identifier from form:", identifier)
        print("password from form:", password)
        customers = load_json(CUSTOMERS_FILE)
        # Admin login using ADMIN_USERNAME and ADMIN_PASSWORD from .env
        if identifier == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['customer_email'] = ADMIN_USERNAME
            return redirect(url_for('dashboard'))
        # Affiliates must use username only
        user = None
        user_email = None
        for email, data in customers.items():
            if identifier == data.get('username'):
                user = data
                user_email = email
                break
        if user and user['password'] == password:
            session['customer_email'] = user_email
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    if 'customer_email' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    result = None
    if request.method == 'POST':
        lookup_type = request.form['lookup_type']
        value = request.form['value']
        customers = load_json(CUSTOMERS_FILE)
        if lookup_type == 'username':
            # Lookup email by username
            email = None
            for e, u in customers.items():
                if u.get('username') == value:
                    email = e
                    break
            if email:
                result = f'Your email is: {email}'
            else:
                result = 'Username not found.'
        elif lookup_type == 'email':
            # Lookup username by email
            user = customers.get(value)
            if user and user.get('username'):
                result = f'Your username is: {user["username"]}'
            else:
                result = 'Email not found.'
    return render_template('forgot.html', result=result)

@app.route('/logout')
def logout():
    session.pop('customer_email', None)
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def dashboard():
    if 'customer_email' not in session:
        return redirect(url_for('login_page'))
    email = session['customer_email']
    customers = load_json(CUSTOMERS_FILE)
    commissions = load_json(COMMISSIONS_FILE)
    customer = customers.get(email, {})
    package_level = customer.get('package_level', 1)
    package_info = get_package_info(package_level)
    accessible_guides = get_accessible_guides(package_level)
    customer_commissions = commissions.get(email, {'total_earned': 0, 'payments': []})
    queue_data = load_json(QUEUE_FILE)
    queue_position = None
    for i, person in enumerate(queue_data.get('queue', [])):
        if person['email'] == email:
            queue_position = i + 1
            break
    # Coey's welcome message and instructions
    coey_message = (
        "<b>Welcome to RizzosAI!</b><br>"
        "Are you ready to earn with RizzosAI? Start by promoting your unique link and forwarding your domain name to your RizzosAI referral link so you get paid for your efforts.<br><br>"
        "<b>How to Get Paid:</b><br>"
        "1. Forward your domain to your RizzosAI referral link.<br>"
        "2. Set up your Stripe account in your profile to receive instant payments.<br>"
        "3. Watch the training videos below for step-by-step instructions on promoting, setting up your domain, and connecting Stripe.<br><br>"
        "Let's get started and make money together!"
    )
    return render_template('dashboard.html',
        customer=customer,
        package_info=package_info,
        accessible_guides=accessible_guides,
        commissions=customer_commissions,
        queue_position=queue_position,
        coey_message=coey_message)

@app.route('/training')
def training():
    if 'customer_email' not in session:
        return redirect(url_for('login_page'))
    email = session['customer_email']
    customers = load_json(CUSTOMERS_FILE)
    customer = customers.get(email, {})
    package_level = customer.get('package_level', 1)
    guides = get_accessible_guides(package_level)
    return render_template('training.html', customer=customer, guides=guides)

@app.route('/queue-dashboard')
def queue_dashboard():
    if 'customer_email' not in session:
        return redirect(url_for('login_page'))
    queue_data = load_json(QUEUE_FILE)
    return render_template('queue_dashboard.html', queue_data=queue_data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form['email']
        password = request.form['password']
        referrer = request.form.get('referrer')
        customers = load_json(CUSTOMERS_FILE)
        # Check for unique and non-empty username
        if not username:
            flash('Username is required.', 'error')
            return redirect(url_for('register'))
        if email in customers or any(u.get('username') == username for u in customers.values()):
            flash('Email or username already registered.', 'error')
            return redirect(url_for('register'))
        # Default package level 1
        customers[email] = {
            'email': email,
            'username': username,
            'password': password,
            'package_level': 1,
            'registered': datetime.utcnow().isoformat(),
            'referrer': referrer
        }
        save_json(CUSTOMERS_FILE, customers)
        add_to_queue(email, referrer)
        # Assign commission to referrer if exists
        if referrer and referrer in customers:
            assign_commission(referrer, 10)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login_page'))
    return render_template('register.html')

@app.route('/change-credentials', methods=['GET', 'POST'])
def change_credentials():
    if 'customer_email' not in session:
        return redirect(url_for('login_page'))
    email = session['customer_email']
    customers = load_json(CUSTOMERS_FILE)
    user = customers.get(email, {})
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        # Check for unique username
        if any(u.get('username') == new_username and e != email for e, u in customers.items()):
            flash('Username already taken.', 'error')
            return redirect(url_for('change_credentials'))
        if new_username:
            user['username'] = new_username
        if new_password:
            user['password'] = new_password
        customers[email] = user
        save_json(CUSTOMERS_FILE, customers)
        flash('Credentials updated successfully.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('change_credentials.html', user=user)

@app.route('/upgrade', methods=['GET', 'POST'])
def upgrade():
    if 'customer_email' not in session:
        return redirect(url_for('login_page'))
    email = session['customer_email']
    customers = load_json(CUSTOMERS_FILE)
    customer = customers.get(email, {})
    current_level = customer.get('package_level', 1)
    packages = load_json(PACKAGES_FILE)
    if request.method == 'POST':
        new_level = int(request.form['package_level'])
        if new_level > current_level and str(new_level) in packages:
            customer['package_level'] = new_level
            customers[email] = customer
            save_json(CUSTOMERS_FILE, customers)
            # Assign commission to referrer if exists and not admin
            referrer = customer.get('referrer')
            if referrer and referrer in customers:
                # Example: $20 commission for upgrade
                assign_commission(referrer, 20)
            flash('Package upgraded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid upgrade selection.', 'error')
    available_packages = [
        {**v, 'level': int(k)} for k, v in packages.items() if int(k) > current_level
    ]
    return render_template('upgrade.html', customer=customer, available_packages=available_packages)

@app.route('/admin')
@admin_required
def admin_dashboard():
    customers = load_json(CUSTOMERS_FILE)
    packages = load_json(PACKAGES_FILE)
    commissions = load_json(COMMISSIONS_FILE)
    queue_data = load_json(QUEUE_FILE)
    return render_template('admin_dashboard.html', customers=customers, packages=packages, commissions=commissions, queue_data=queue_data)

@app.route('/admin/remove-user/<email>', methods=['POST'])
@admin_required
def remove_user(email):
    customers = load_json(CUSTOMERS_FILE)
    if email in customers and email != 'admin@rizzosai.com':
        del customers[email]
        save_json(CUSTOMERS_FILE, customers)
        flash(f'User {email} removed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update-package', methods=['POST'])
@admin_required
def update_package():
    packages = load_json(PACKAGES_FILE)
    level = request.form['level']
    name = request.form['name']
    price = float(request.form['price'])
    guide_count = int(request.form['guide_count'])
    packages[level] = {'name': name, 'price': price, 'guide_count': guide_count}
    save_json(PACKAGES_FILE, packages)
    flash(f'Package {name} updated.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/remove-from-queue/<email>', methods=['POST'])
@admin_required
def remove_from_queue(email):
    queue_data = load_json(QUEUE_FILE)
    queue = queue_data.get('queue', [])
    queue = [person for person in queue if person['email'] != email]
    queue_data['queue'] = queue
    save_json(QUEUE_FILE, queue_data)
    flash(f'{email} removed from queue.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reset-commissions/<email>', methods=['POST'])
@admin_required
def reset_commissions(email):
    commissions = load_json(COMMISSIONS_FILE)
    if email in commissions:
        commissions[email]['total_earned'] = 0
        commissions[email]['payments'] = []
        save_json(COMMISSIONS_FILE, commissions)
        flash(f'Commissions reset for {email}.', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
