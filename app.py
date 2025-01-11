from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import MySQLdb.cursors
import os
app = Flask(__name__)

# Configure MySQL
# MySQL configuration
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))  # Default to 3306 if not specified
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

app.secret_key = secrets.token_hex(16)



mysql = MySQL(app)

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

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (full_name,user_name, email, user_password, mobile_no, place,admin_name) VALUES (%s, %s, %s, %s, %s, %s,%s)", 
                       (full_name, user_name, email,hashed_password, mobile_no, place,admin_name))
        mysql.connection.commit()
        cursor.close()
        
        flash('User registered successfully!', 'success')
        return render_template('user_signin.html')
    return render_template('user_signup.html')

# User Login Route
@app.route('/user-signin', methods=['GET', 'POST'])
def user_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['user_password'], password):
            # Store user information in session
            session['user_id'] = user['user_id']  # Replace 'id' with the actual column name for the user ID
            session['user_name'] = user['user_name']
              # Replace 'user_name' with the actual column name for the username
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
        user_name =request.form['username']
        email = request.form['email']
        admin_password = request.form['password']
        
        
        
        # Hash the password
        hashed_password = generate_password_hash(admin_password)

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO admins (full_name, user_name, email,admin_password) VALUES (%s, %s, %s, %s)", 
                       (full_name,user_name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        
        flash('Admin registered successfully!', 'success')
        return  render_template('admin_signin.html')
    return render_template('admin_signup.html')

# Admin Login Route
@app.route('/admin-signin', methods=['GET', 'POST'])
def admin_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        
        cursor.close()

        if email == "example@gmail.com" and password == "1234":  # admin[2] is the password field
            
             # Store admin ID in session
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
    return  render_template('home.html')

@app.route('/submit_work_log', methods=['POST'])
def submit_work_log():
    if request.method == 'POST':
        # Ensure the user is logged in
        if 'user_id' not in session or 'user_name' not in session:
            flash('You need to log in first!', 'danger')
            return redirect('/user-signin')

        # Get form data
        name = request.form['name']
        place = request.form['place']
        phone = request.form['phone']
        machine = request.form['machine']  # Get selected machine
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        work_details = request.form['work_details']
        
        # Calculate time worked and amount
        time_worked = float(end_time) - float(start_time)
        if machine == '70':
            amount = time_worked * 1700
        elif machine == '120':
            amount = time_worked * 2000
        elif machine == 'JCB':
            amount = time_worked  * 1800
        else:
            amount = 0

        # Get user information from session
        user_id = session['user_id']
        user_name = session['user_name']

        # Insert work log into the database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('''
            INSERT INTO work_logs (name, place, phone, machine, date, start_time, end_time, work_details, time_worked, user_name, user_id, amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (name, place, phone, machine, date, start_time, end_time, work_details, time_worked, user_name, user_id, amount))
        mysql.connection.commit()
        cur.close()

        flash('Work log submitted successfully!', 'success')
        return render_template('user_index.html')
    
@app.route('/admin_user_details', methods=['GET', 'POST'])
def admin_user_details():
    # Ensure the admin is logged in
    if 'user_name' not in session:
        flash('You need to log in first!', 'danger')
        return redirect('/admin_signin')

    admin_name = session['user_name']

    print(f"Admin Name from session: {admin_name}")

    # Query the database for users associated with this admin
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT full_name, email, mobile_no, place, created_at
        FROM users
        WHERE admin_name = %s
    ''', (admin_name,))
    
    users = cur.fetchall()
    cur.close()

    # Check if users were found
    if not users:
        flash('No users found for this admin.', 'warning')

    # Render the admin view template
    return render_template('admin_user_details.html', users=users, admin_name=admin_name)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # Ensure the admin is logged in (add your authentication logic here)

    # Get the date filter parameter from the request
    date_filter = request.args.get('date', None)

    # Fetch data for visualization
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Build query condition for date filter
    where_clause = "WHERE DATE(date) = %s" if date_filter else ""
    query_params = [date_filter] if date_filter else []

    # Total work logs by machine (in hours)
    cur.execute(f'''
        SELECT machine, SUM(time_worked) as total_hours 
        FROM work_logs
        {where_clause}
        GROUP BY machine
    ''', query_params)
    machine_hours = cur.fetchall()

    # Total earnings by machine
    cur.execute(f'''
        SELECT machine, SUM(amount) as total_amount 
        FROM work_logs
        {where_clause}
        GROUP BY machine
    ''', query_params)
    machine_earnings = cur.fetchall()

    # Work logs per user (in hours)
    cur.execute(f'''
        SELECT user_name, SUM(time_worked) as total_hours 
        FROM work_logs
        {where_clause}
        GROUP BY user_name
    ''', query_params)
    user_hours = cur.fetchall()

    cur.close()

    # Prepare data for charts
    machine_hours_data = {
        "labels": [row['machine'] for row in machine_hours],
        "data": [row['total_hours'] for row in machine_hours]
    }

    total_earnings = sum(row['total_amount'] for row in machine_earnings) or 1  # Avoid division by zero
    earnings_percentage_data = {
        "labels": [row['machine'] for row in machine_earnings],
        "data": [row['total_amount'] for row in machine_earnings]
    }

    user_hours_data = {
        "labels": [row['user_name'] for row in user_hours],
        "data": [row['total_hours'] for row in user_hours]
    }

    return render_template(
        'dashboard.html',
        machine_hours_data=machine_hours_data,
        earnings_percentage_data=earnings_percentage_data,
        user_hours_data=user_hours_data,
        filters={"date": date_filter}
    )



@app.route('/admin_index', methods=['GET'])
def admin_index():
    user_name = request.args.get('user_name')
    date = request.args.get('date')
    machine = request.args.get('machine')
    name = request.args.get('name')

    query = "SELECT * FROM work_logs WHERE 1=1";  # Base query to fetch all work logs

    # Apply filters if provided
    params = []
    if user_name:
        query += " AND user_name LIKE %s"
        params.append(f"%{user_name}%")
    if date:
        query += " AND date = %s"
        params.append(date)
    if machine:
        query += " AND machine = %s"
        params.append(machine)
    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query, tuple(params))
    work_logs = cursor.fetchall()
    cursor.close()
    # Dynamically calculate amount if missing # Append the amount to the tuple

# Now updated_work_logs contains tuples with the 'amount' appended at the end
    return render_template('admin_index.html', work_logs=work_logs)


if __name__ == '__main__':
    app.run(debug=True)
