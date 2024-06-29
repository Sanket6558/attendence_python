from flask import Flask, request, jsonify, render_template
import mysql.connector
from urllib.parse import quote
from geopy.distance import geodesic
from datetime import datetime, timedelta

app = Flask(__name__)

# Office location coordinates
office_location = (18.6161, 73.7286)  #room
#office_location = (16.834814, 74.6517426)  #office

# Define the MySQL connection
db_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'attendance_db_new'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    emp_id = request.form['emp_id']
    access_code = request.form['access_code']
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM employees WHERE emp_id = %s AND access_code = %s"
    cursor.execute(query, (emp_id, access_code))
    employee = cursor.fetchone()
    
    if employee:
        return jsonify({
            'status': 'success',    
            'employee': employee
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid Employee ID or Access Code'
        })

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    emp_id = request.form['emp_id']
    access_code = request.form['access_code']
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        query = "INSERT INTO employees (emp_id, name, access_code) VALUES (%s, %s, %s)"
        cursor.execute(query, (int(emp_id), name, access_code))
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User Registered Successfully'
        })
    except mysql.connector.Error as err:
        return jsonify({
            'status': 'error',
            'message': str(err)
        })

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    emp_id = request.form['emp_id']
    location = request.form['location'].split(',')
    current_location = (float(location[0]), float(location[1]))
    
    # Calculate distance from office location
    dist = geodesic(office_location, current_location).meters
    
    if dist <= 1000:  # 1km radius (1000 meters)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM employees WHERE emp_id = %s"
        cursor.execute(query, (emp_id,))
        employee = cursor.fetchone()
        
        if employee:
            # Store attendance time in database
            now = datetime.now()
            formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
            
            query = "INSERT INTO attendance (emp_id, attendance_time) VALUES (%s, %s)"
            cursor.execute(query, (emp_id, formatted_date))
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Attendance marked successfully',
                'attendance_time': formatted_date  # Return the formatted date as a string
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Employee not found'
            })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Not within attendance radius (1km from office)'
        })

@app.route('/sign_out', methods=['POST'])
def sign_out():
    emp_id = request.form['emp_id']
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Find the latest attendance record for the employee
    query = "SELECT * FROM attendance WHERE emp_id = %s ORDER BY attendance_time DESC LIMIT 1"
    cursor.execute(query, (emp_id,))
    attendance_record = cursor.fetchone()
    
    if attendance_record:
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update the attendance record with sign-out time
        query = "UPDATE attendance SET sign_out_time = %s WHERE id = %s"
        cursor.execute(query, (formatted_date, attendance_record['id']))
        conn.commit()
        
        # Calculate time spent
        attendance_time_obj = attendance_record['attendance_time']  # This is already a datetime object
        sign_out_time = datetime.strptime(formatted_date, '%Y-%m-%d %H:%M:%S')
        time_spent = sign_out_time - attendance_time_obj
        
        # Convert time spent to total seconds
        total_seconds = int(time_spent.total_seconds())
        
        # Convert total seconds to HH:MM:SS format
        total_time = str(timedelta(seconds=total_seconds))
        
        # Update total_time in database
        update_query = "UPDATE attendance SET total_time = %s WHERE id = %s"
        cursor.execute(update_query, (total_time, attendance_record['id']))
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Signed out successfully',
            'time_spent': total_time
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'No attendance record found'
        })

@app.route('/update_location', methods=['POST'])
def update_location():
    emp_id = request.form['emp_id']
    location = request.form['location'].split(',')
    current_location = (float(location[0]), float(location[1]))
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    query = "INSERT INTO location_tracking (emp_id, latitude, longitude, timestamp) VALUES (%s, %s, %s, %s)"
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(query, (emp_id, current_location[0], current_location[1], now))
    conn.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Location updated successfully'
    })

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return app.send_static_file('service-worker.js')

@app.route('/check_location', methods=['POST'])
def check_location():
    emp_id = request.form['emp_id']
    location = request.form['location'].split(',')
    current_location = (float(location[0]), float(location[1]))
    
    # Calculate distance from office location
    dist = geodesic(office_location, current_location).meters
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Get the latest attendance record for the employee
    query = "SELECT * FROM attendance WHERE emp_id = %s ORDER BY attendance_time DESC LIMIT 1"
    cursor.execute(query, (emp_id,))
    attendance_record = cursor.fetchone()
    
    if not attendance_record:
        return jsonify({'status': 'error', 'message': 'No attendance record found'})

    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    
    if dist <= 1000:  # 1km radius
        if attendance_record['status'] == 'paused':
            # Resume timer
            paused_duration = now - attendance_record['pause_time']
            new_attendance_time = attendance_record['attendance_time'] + paused_duration
            
            update_query = "UPDATE attendance SET attendance_time = %s, status = %s, pause_time = NULL WHERE id = %s"
            cursor.execute(update_query, (new_attendance_time, 'active', attendance_record['id']))
            conn.commit()
        
        return jsonify({'status': 'inside', 'message': 'Employee is inside the radius'})
    else:
        if attendance_record['status'] == 'active':
            # Pause timer
            update_query = "UPDATE attendance SET pause_time = %s, status = %s WHERE id = %s"
            cursor.execute(update_query, (formatted_date, 'paused', attendance_record['id']))
            conn.commit()
        
        return jsonify({'status': 'outside', 'message': 'Employee is outside the radius'})
