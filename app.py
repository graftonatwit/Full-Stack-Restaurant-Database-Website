
import os

from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from datetime import datetime
from flask import Flask, render_template, redirect, session
from face_auth import authenticate_user
from PIL import Image
import io
import numpy as np
import face_recognition
import re

app = Flask(__name__)
app.secret_key = "supersecretkey" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACE_PATH = os.path.join("static", "my_face.jpeg") # Make sure this path is correct

# Load known face encoding once at startup
known_image = face_recognition.load_image_file(KNOWN_FACE_PATH) # Make sure this path is correct and the image exists
known_encodings = face_recognition.face_encodings(known_image) # Check if a face was found in the known image
if len(known_encodings) == 0:
    raise Exception("No face found in known image")
KNOWN_ENCODING = known_encodings[0]
# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@flag961TOAD",
        database="myrestaurantdb"
    )
    

@app.route("/face_login", methods=["GET", "POST"])
def face_login():
    if request.method == "POST":
        if 'image' not in request.files:
            return "No image uploaded", 400

        file = request.files['image']
        unknown_image = face_recognition.load_image_file(file)

        # Encode faces in the uploaded image
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if len(unknown_encodings) == 0:
            return "No face detected in camera image", 400

        # Compare uploaded faces with known face
        for encoding in unknown_encodings:
            matches = face_recognition.compare_faces([KNOWN_ENCODING], encoding)
            if True in matches:
                session["logged_in"] = True
                return """
                    
                    <script>
                        setTimeout(() => { window.location.href = '/'; }, 1000);
                    </script>
                """

        return "Face not recognized"

    # GET request: render the login page
    return render_template("face_login.html")
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect("/face_login")
    return """
        <h1>Welcome to Trevor's Restaurant Management System!</h1>
        <p>You are logged in.</p>
        <a href= "/index">Go to homepage</a><br>
        <a href="/logout">Logout</a>
    """

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/face_login")


# Home page
@app.route('/index')
def index():
    return render_template('index.html')

# Show all customers
@app.route('/customers')
def customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)
@app.route('/menu')
def menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM MenuItem")
    items = cursor.fetchall()
    conn.close()
    return render_template('menu.html', items=items)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    name = request.form['name']
    description = request.form['description']
    Price = request.form['Price']
    
    errors = [] # List to hold error messages
    
    if not name or not description or not Price:
        errors.append('Please fill in all fields.')
        
    if not name.replace(" ", "").replace("-", "").isalpha():
        errors.append('Menu item name cannot contain numbers.', )

    if not description.replace(" ", "").replace("-", "").replace(".", "").replace(",", "").replace("!", "").replace("?", "").isalpha():
        errors.append('Menu item description cannot contain numbers.')

    try:
        price = float(Price)
        if price < 0:
            errors.append("Price must be positive.")
    except ValueError:
        errors.append("Price must be a valid number (e.g., 12.99).")

        
    if errors:
        for error in errors:
            flash(error)
        return redirect('/menu')

    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO MenuItem (name, description, Price)
        VALUES (%s, %s, %s)
    """, (name, description, Price))
    conn.commit()
    conn.close()
    return redirect('/menu')
@app.route("/delete_menu_item/<int:item_id>", methods=["POST"])
def delete_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    #cursor.execute("DELETE FROM OrderItem WHERE menu_item_id = %s", (item_id,))
    cursor.execute("DELETE FROM MenuItem WHERE menu_item_id = %s", (item_id,))

    conn.commit()
    conn.close()
    flash("Menu item deleted successfully.")
    return redirect("/menu")


# Add customer form
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        print("FORM SUBMITTED")
        first = request.form['first_name']
        last = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        errors = []
        if not first:
            errors.append("First name is required.")
        if not last:
            errors.append("Last name is required.")
        if not phone:
            errors.append("Phone is required.")
        if not email:
            errors.append("Email is required.")
        if not re.fullmatch(r"[A-Za-z]+", first):
            errors.append('First name cannot contain numbers, spaces, or special characters.')

        if not re.fullmatch(r"[A-Za-z]+", last  ):
            errors.append('Last name cannot contain numbers, spaces, or special characters.')
        
        if not re.fullmatch(r"\d{10}", phone):
            errors.append("Invalid phone number. Must be 10 digits.") 
        if errors:
            # Flash all errors and stay on the same page
            for error in errors:
                flash(error)
            return render_template("customers.html")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Customer (first_name, last_name, phone_number, email)
            VALUES (%s, %s, %s, %s)
        """, (first, last, phone, email))
        conn.commit()
        conn.close()

        return redirect('/customers')

    return render_template('add_customer.html')

@app.route("/delete_customer/<int:customer_id>", methods=["POST"]) 
def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete related reservations first
    cursor.execute("DELETE FROM Reservation WHERE Customer_customer_id = %s", (customer_id,))
    
    # Now delete the customer
    cursor.execute("DELETE FROM Customer WHERE customer_id = %s", (customer_id,)) 

    conn.commit()
    conn.close()
    flash("Customer deleted successfully.")
    return redirect("/customers")

@app.route("/update_customer/<int:id>", methods=["GET", "POST"])
def update_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        errors = []

        # validation
        if not first:
            errors.append("First name is required.")
        if not last:
            errors.append("Last name is required.")
        if not phone:
            errors.append("Phone is required.")
        if not email:
            errors.append("Email is required.")
        if not re.fullmatch(r"[A-Za-z]+", first):
            errors.append("First name cannot contain numbers, spaces, or special characters.")
        if not re.fullmatch(r"[A-Za-z]+", last):
            errors.append("Last name cannot contain numbers, spaces, or special characters.")
        if not re.fullmatch(r"\d{10}", phone):
            errors.append("Invalid phone number. Must be 10 digits.") 

        if errors:
            for error in errors:
                flash(error)
            cursor.execute("SELECT * FROM customer WHERE customer_id=%s", (id,))
            customer = cursor.fetchone()
            return render_template("update_customer.html", customer=customer)

        # update DB
        cursor.execute("""
            UPDATE customer
            SET first_name=%s, last_name=%s, phone_number=%s, email=%s
            WHERE customer_id=%s
        """, (first, last, phone, email, id))
        conn.commit()

        # flash success and redirect to main page
        flash("Customer updated successfully.")
        return redirect("/customers")  # <-- goes to main page

    # GET request → show update form
    cursor.execute("SELECT * FROM customer WHERE customer_id=%s", (id,))
    customer = cursor.fetchone()
    return render_template("update_customer.html", customer=customer)

@app.route('/reservations')
def reservations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.reservation_id, r.reservation_date, r.party_size, r.Customer_customer_id, c.first_name, c.last_name
        FROM Reservation r
        JOIN Customer c ON r.Customer_customer_id = c.customer_id
    """)
    reservations = cursor.fetchall()
    cursor.execute("SELECT customer_id, first_name, last_name From customer")
    customers = cursor.fetchall()
    conn.close()
    return render_template('reservations.html', reservations=reservations, customers=customers)
@app.route('/add_reservation_item', methods=['POST'])
def add_reservation_item():
    customer_id = request.form.get('customer_id')
    if not customer_id:
        print("Please select a customer.")
        return redirect('/reservations')
    reservation_date = request.form['reservation_date']
    party_size = request.form['party_size']
    
    errors = []
    from datetime import datetime, date
    if reservation_date:
        try:
            res_date = datetime.strptime(reservation_date, "%Y-%m-%d").date()
            if res_date < date.today():
                errors.append("Reservation date cannot be in the past.")
        except ValueError:
            errors.append("Invalid date format.")
    if party_size == "":
        errors.append("Please enter a party size.")
    elif not party_size.isdigit():
        errors.append("Party size must be a number.")
    elif int(party_size) < 1:
        errors.append("Party size must be at least 1.")
    elif int(party_size) > 15:
        errors.append("Party size must be at most 15.")

    if reservation_date == "":
        errors.append("Please enter a reservation date.")

    if errors:
        for e in errors:
            flash(e)
        return redirect('/reservations')
    

    reservation_date = datetime.strptime(reservation_date, "%Y-%m-%d").strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD format()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Customer WHERE customer_id = %s", (customer_id,))
    if cursor.fetchone() is None:
        print("Selected customer does not exist.")
        conn.close()
        return redirect('/reservations')
    cursor.execute("""
        INSERT INTO Reservation (Customer_customer_id, reservation_date, party_size)
        VALUES (%s, %s, %s)
    """, (customer_id, reservation_date, party_size))
    conn.commit()
    conn.close()
    return redirect('/reservations')

@app.route("/delete_reservation_item/<int:reservation_id>", methods=["POST"])
def delete_reservation_item(reservation_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    #cursor.execute("DELETE FROM OrderItem WHERE reservation_id = %s", (reservation_id,))
    cursor.execute("DELETE FROM Reservation WHERE reservation_id = %s", (reservation_id,))

    conn.commit()
    conn.close()
    flash("Reservation deleted successfully.")
    return redirect("/reservations")


@app.route("/update_reservation/<int:id>", methods=["GET", "POST"])
def update_reservation(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the reservation with customer info
    cursor.execute("""
        SELECT r.reservation_id, r.Customer_customer_id, r.reservation_date, r.party_size,
        c.first_name, c.last_name
        FROM reservation r
        JOIN customer c ON r.Customer_customer_id = c.customer_id
        WHERE r.reservation_id = %s
    """, (id,))
    reservation = cursor.fetchone()

    if reservation is None:
        flash("Reservation not found.")
        return redirect("/reservations")

    if request.method == "POST":
        # Only these fields are editable
        reservation_date = request.form.get("reservation_date")
        party_size = request.form.get("party_size")

        errors = []

        # Validation
        if not reservation_date:
            errors.append("Reservation date is required.")
        if party_size > 15:
            errors.append("Party size must be less than or equal to 15.")
        if not party_size:
            errors.append("Party size is required.")
        else:
            try:
                party_size_int = int(party_size)
                if party_size_int <= 0:
                    errors.append("Party size must be greater than 0.")
            except ValueError:
                errors.append("Party size must be a number.")

        # Optional: ensure reservation date is not in the past
        from datetime import datetime, date
        if reservation_date:
            try:
                res_date = datetime.strptime(reservation_date, "%Y-%m-%d").date()
                if res_date < date.today():
                    errors.append("Reservation date cannot be in the past.")
            except ValueError:
                errors.append("Invalid date format.")

        if errors:
            # Flash all errors and stay on the same page
            for error in errors:
                flash(error)
            return render_template("update_reservation.html", reservation=reservation)

        # If valid, update the reservation
        cursor.execute("""
            UPDATE reservation
            SET reservation_date=%s,
                party_size=%s
            WHERE reservation_id=%s
        """, (reservation_date, party_size_int, id))
        conn.commit()
        flash("Reservation updated successfully.")
        conn.close()
        return redirect("/reservations")

    conn.close()
    return render_template("update_reservation.html", reservation=reservation)


@app.route("/employees")
def employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Employee")
    employees = cursor.fetchall()
    conn.close()
    return render_template('employees.html', employees=employees)

@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        role = request.form["role"]
        hire_date = request.form["hire_date"]
        errors = []

        # Validation
        if not first:
            errors.append("First name is required.")
        if not last:
            errors.append("Last name is required.")
        if not role:
            errors.append("Role is required.")
        if not hire_date:
            errors.append("Hire date is required.")
        if not re.fullmatch(r"[A-Za-z]+", first):
            errors.append('First name cannot contain numbers, spaces, or special characters.')

        if not re.fullmatch(r"[A-Za-z]+", last  ):
            errors.append('Last name cannot contain numbers, spaces, or special characters.')
            
        if errors:
            # Flash all errors and stay on the same page
            for error in errors:
                flash(error)
            return render_template("add_employee.html")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Employee (first_name, last_name, role, hire_date) VALUES (%s, %s, %s, %s)", (first, last, role, hire_date))
        conn.commit()
        conn.close()

        return redirect("/employees")

    return render_template("add_employee.html")


@app.route("/update_employee/<int:id>", methods=["GET", "POST"])
def update_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get the employee info
    cursor.execute("SELECT * FROM Employee WHERE employee_id = %s", (id,))
    employee = cursor.fetchone()

    
    if employee is None:
        flash("Employee not found.")
        return redirect("/employees")
    
    

    if request.method == "POST":
        first = request.form["first_name"]
        last = request.form["last_name"]
        role = request.form["role"]
        hire_date = request.form["hire_date"]
        
        errors = []
        if not first:
            errors.append("First name is required.")
        if not last:
            errors.append("Last name is required.")
        if not role:
            errors.append("Role is required.")
        if not hire_date:
            errors.append("Hire date is required.")
        if not re.fullmatch(r"[A-Za-z]+", first):
            errors.append('First name cannot contain numbers, spaces, or special characters.')

        if not re.fullmatch(r"[A-Za-z]+", last  ):
            errors.append('Last name cannot contain numbers, spaces, or special characters.')
                
        if errors:
            # Flash all errors and stay on the same page
            for error in errors:
                flash(error)
            return render_template("update_employee.html", employee=employee)

        cursor.execute("UPDATE Employee SET first_name=%s, last_name=%s, role=%s, hire_date=%s WHERE employee_id=%s", (first, last, role, hire_date, id))
        conn.commit()
        conn.close()
        flash("Employee updated successfully.")
        return redirect("/employees")

    conn.close()
    return render_template("update_employee.html", employee=employee)


@app.route("/delete_employee/<int:id>", methods=["POST"])
def delete_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Employee WHERE employee_id = %s", (id,))
    conn.commit()
    conn.close()
    flash("Employee deleted successfully.")
    return redirect("/employees")

if __name__ == '__main__':
    app.run(debug=True)
