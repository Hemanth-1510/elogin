from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from pymongo import MongoClient
import os

app = Flask(__name__)

# Configure MongoDB
uri = "mongodb+srv://addagadahemanth:Hemanth21@cluster0.iyynh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['elogin']  # Replace with your database name

app.secret_key = secrets.token_hex(16)

@app.route('/')
def index():
    return render_template('home.html')

# User Signup Route
@app.route('/user-signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        full_name = request.form['fullname']
        user_name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        mobile_no = request.form['mobile']
        place = request.form['place']
        admin_name = request.form['adminname']

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert user into MongoDB
        db.users.insert_one({
            "full_name": full_name,
            "user_name": user_name,
            "email": email,
            "user_password": hashed_password,
            "mobile_no": mobile_no,
            "place": place,
            "admin_name": admin_name
        })

        flash('User registered successfully!', 'success')
        return render_template('user_signin.html')
    return render_template('user_signup.html')

# User Login Route
@app.route('/user-signin', methods=['GET', 'POST'])
def user_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = db.users.find_one({"email": email})

        if user and check_password_hash(user['user_password'], password):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['user_name']
            flash('User login successful!', 'success')
            return render_template('user_index.html')
        else:
            flash('Invalid email or password', 'danger')
            return render_template('user_signin.html')
    return render_template('user_signin.html')

# Admin Signup Route
@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        full_name = request.form['fullname']
        user_name = request.form['username']
        email = request.form['email']
        admin_password = request.form['password']

        # Hash the password
        hashed_password = generate_password_hash(admin_password)

        # Insert admin into MongoDB
        db.admins.insert_one({
            "full_name": full_name,
            "user_name": user_name,
            "email": email,
            "admin_password": hashed_password
        })

        flash('Admin registered successfully!', 'success')
        return render_template('admin_signin.html')
    return render_template('admin_signup.html')

# Admin Login Route

@app.route('/admin-signin', methods=['GET', 'POST'])
def admin_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Hardcoded admin credentials
        hardcoded_email = "example@gmail.com"
        hardcoded_password = "1234"

        if email == hardcoded_email and password == hardcoded_password:
            # Store admin details in the session
            session['admin_id'] = "1"  # Assign a dummy admin ID
            session['admin_name'] = "Super Admin"
            flash('Admin login successful!', 'success')
            return render_template('admin_user_details.html')
        else:
            flash('Invalid email or password', 'danger')
            return render_template('admin_signin.html')
    return render_template('admin_signin.html')


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return render_template('home.html')

@app.route('/submit_work_log', methods=['POST'])
def submit_work_log():
    if 'user_id' not in session or 'user_name' not in session:
        flash('You need to log in first!', 'danger')
        return redirect('/user-signin')

    name = request.form['name']
    place = request.form['place']
    phone = request.form['phone']
    machine = request.form['machine']
    date = request.form['date']
    start_time = float(request.form['start_time'])
    end_time = float(request.form['end_time'])
    work_details = request.form['work_details']

    time_worked = end_time - start_time
    rates = {"70": 1700, "120": 2000, "JCB": 1800}
    time_worked= time_worked/6
    amount = time_worked * rates.get(machine, 0)

    db.work_logs.insert_one({
        "name": name,
        "place": place,
        "phone": phone,
        "machine": machine,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "work_details": work_details,
        "time_worked": time_worked,
        "user_name": session['user_name'],
        "user_id": session['user_id'],
        "amount": amount
    })

    flash('Work log submitted successfully!', 'success')
    return render_template('user_index.html')

@app.route('/admin_user_details', methods=['GET'])
def admin_user_details():
    if 'admin_name' not in session:
        flash('You need to log in first!', 'danger')
        return redirect('/admin-signin')

    admin_name = session['admin_name']
    users = list(db.users.find({"admin_name": admin_name}, {"_id": 0}))

    return render_template('admin_user_details.html', users=users, admin_name=admin_name)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    date_filter = request.args.get('date')
    query = {"date": date_filter} if date_filter else {}

    machine_hours = list(db.work_logs.aggregate([
        {"$match": query},
        {"$group": {"_id": "$machine", "total_hours": {"$sum": "$time_worked"}}}
    ]))

    machine_earnings = list(db.work_logs.aggregate([
        {"$match": query},
        {"$group": {"_id": "$machine", "total_amount": {"$sum": "$amount"}}}
    ]))

    user_hours = list(db.work_logs.aggregate([
        {"$match": query},
        {"$group": {"_id": "$user_name", "total_hours": {"$sum": "$time_worked"}}}
    ]))

    return render_template(
        'dashboard.html',
        machine_hours_data={"labels": [x["_id"] for x in machine_hours], "data": [x["total_hours"] for x in machine_hours]},
        earnings_percentage_data={"labels": [x["_id"] for x in machine_earnings], "data": [x["total_amount"] for x in machine_earnings]},
        user_hours_data={"labels": [x["_id"] for x in user_hours], "data": [x["total_hours"] for x in user_hours]},
        filters={"date": date_filter}
    )
    


@app.route('/admin_index', methods=['GET'])
def admin_index():
    # Ensure the admin is logged in
    if 'admin_name' not in session:
        flash('You need to log in first!', 'danger')
        return redirect('/admin-signin')

    # Get filter parameters from the request
    user_name = request.args.get('user_name')
    date = request.args.get('date')
    machine = request.args.get('machine')
    name = request.args.get('name')

    # Build query filters dynamically
    query = {}
    if user_name:
        query['user_name'] = {"$regex": user_name, "$options": "i"}  # Case-insensitive regex
    if date:
        query['date'] = date
    if machine:
        query['machine'] = machine
    if name:
        query['name'] = {"$regex": name, "$options": "i"}  # Case-insensitive regex

    # Fetch work logs from MongoDB
    work_logs = list(db.work_logs.find(query))

    # Add computed fields (if needed)
    for log in work_logs:
        log['time_worked'] = log.get('end_time', 0) - log.get('start_time', 0)
        rates = {"70": 1700, "120": 2000, "JCB": 1800}
        log['amount'] = log['time_worked'] * rates.get(log.get('machine'), 0)

    return render_template('admin_index.html', work_logs=work_logs)


if __name__ == '__main__':
    app.run(debug=True)
