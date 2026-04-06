
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
from werkzeug.security import generate_password_hash, check_password_hash

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
        password="DB_PASSWORD",
        database="restaurantdb"
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
                return "Face recognized"

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
    Price = request.form['price']
    
    errors = [] # List to hold error messages
    
    # Validation
    if not name:
        errors.append("Name is required.")
    if not description:
        errors.append("Description is required.")
    if not Price:
        errors.append("Price is required.")

    if name and not name.replace(" ", "").replace("-", "").isalpha():
        errors.append("Menu item name cannot contain numbers or special characters.")

    # Allow standard punctuation in description
    if description and not re.fullmatch(r"[A-Za-z0-9\s.,!?'-]+", description):
        errors.append("Description contains invalid characters.")

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
        INSERT INTO MenuItem (name, description, price)
        VALUES (%s, %s, %s)
    """, (name, description, Price))
    conn.commit()
    conn.close()
    return redirect('/menu')
@app.route("/delete_menu_item/<int:item_id>", methods=["POST"])
def delete_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find all orders that include this menu item
    cursor.execute("""
        SELECT DISTINCT Order_order_id 
        FROM OrderItem 
        WHERE MenuItem_menu_item_id = %s
    """, (item_id,))
    order_ids = cursor.fetchall()  # list of tuples

    if order_ids:
        # Update status to 'Cancelled' in the Order table
        cursor.executemany("""
            UPDATE `Order`
            SET status = 'Cancelled'
            WHERE order_id = %s
        """, order_ids)

        # Delete related OrderItems
        cursor.execute("""
            DELETE FROM OrderItem
            WHERE MenuItem_menu_item_id = %s
        """, (item_id,))

    # Now safe to delete menu item
    cursor.execute("DELETE FROM MenuItem WHERE menu_item_id = %s", (item_id,))

    conn.commit()
    conn.close()
    flash("Menu item deleted and related orders cancelled.")
    return redirect("/menu")

@app.route("/update_menu_item/<int:item_id>", methods=["GET", "POST"])
def update_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the current item
    cursor.execute("SELECT * FROM MenuItem WHERE menu_item_id = %s", (item_id,))
    item = cursor.fetchone()
    if item is None:
        flash("Menu item not found.")
        conn.close()
        return redirect("/menu")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_input = request.form.get("price", "").strip()
        errors = []
        # Validation
        if not name:
            errors.append("Name is required.")
        if not description:
            errors.append("Description is required.")
        if not price_input:
            errors.append("Price is required.")

        if name and not name.replace(" ", "").replace("-", "").isalpha():
            errors.append("Menu item name cannot contain numbers or special characters.")

        # Allow standard punctuation in description
        if description and not re.fullmatch(r"[A-Za-z0-9\s.,!?'-]+", description):
            errors.append("Description contains invalid characters.")

        try:
            price = float(price_input)
            if price < 0:
                errors.append("Price must be positive.")
        except ValueError:
            errors.append("Price must be a valid number (e.g., 12.99).")

        if errors:
            for error in errors:
                flash(error)
            # Render the form again with previous values
            return render_template("update_menu.html", item={"menu_item_id": item_id, "name": name, "description": description, "Price": price_input})

        # Update in database
        cursor.execute("""
            UPDATE MenuItem
            SET name = %s, description = %s, price = %s
            WHERE menu_item_id = %s
        """, (name, description, price, item_id))
        conn.commit()
        conn.close()

        flash("Menu item updated successfully.")
        return redirect("/menu")

    conn.close()
    # GET request → show the form
    return render_template("update_menu.html", item=item)

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
        SELECT r.reservation_id, r.reservation_date, r.party_size, r.Customer_customer_id, 
            r.DiningTable_table_id, c.first_name, c.last_name, d.table_number
        FROM Reservation r
        JOIN Customer c ON r.Customer_customer_id = c.customer_id
        JOIN DiningTable d ON r.DiningTable_table_id = d.table_id
    """)
    # Get all reservations
    reservations = cursor.fetchall()
    cursor.execute("SELECT customer_id, first_name, last_name From customer")
    customers = cursor.fetchall()
    # Get all tables
    cursor.execute("SELECT table_id, table_number, capacity FROM DiningTable")
    tables = cursor.fetchall()
    conn.close()
    return render_template('reservations.html', reservations=reservations, customers=customers, tables=tables)
@app.route('/add_reservation_item', methods=['POST'])
def add_reservation_item():
    customer_id = request.form.get('customer_id')
    table_id = request.form.get('table_id')
    reservation_date = request.form['reservation_date']
    party_size = request.form['party_size']
    
    
    errors = []
    
    if not customer_id:
        errors.append("Please select a customer.")
    if not table_id:
        errors.append("Please select a table.")
    if not reservation_date:
        errors.append("Please enter a reservation date.")
    if not party_size or not party_size.isdigit() or int(party_size) < 1:
        errors.append("Invalid party size. Must be a positive number.")
        
    
    from datetime import datetime, date
    if reservation_date:
        try:
            res_date = datetime.strptime(reservation_date, "%Y-%m-%d").date()
            if res_date < date.today():
                errors.append("Reservation date cannot be in the past.")
        except ValueError:
            errors.append("Invalid date format.")
    if errors:
        for e in errors:
            flash(e)
        return redirect('/reservations')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
        
    

    reservation_date = datetime.strptime(reservation_date, "%Y-%m-%d").strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD format()


    # Check if customer exists
    cursor.execute("SELECT 1 FROM Customer WHERE customer_id = %s", (customer_id,))
    if cursor.fetchone() is None:
        print("Selected customer does not exist.")
        conn.close()
        return redirect('/reservations')
    
    # Get the table capacity
    cursor.execute("SELECT capacity FROM DiningTable WHERE table_id = %s", (table_id,))
    
    table = cursor.fetchone()
    if table is None:
        flash("Selected table does not exist.")
        conn.close()
        return redirect('/reservations')

    table_capacity = table['capacity']  # assuming cursor is dictionary=True
    
    if int(party_size) > table_capacity:
        flash(f"Party size cannot exceed table capacity ({table_capacity}).")
        conn.close()
        return redirect('/reservations')
    
    # Check if table exists
    cursor.execute("SELECT 1 FROM DiningTable WHERE table_id = %s", (table_id,))
    if cursor.fetchone() is None:
        flash("Selected table does not exist.")
        conn.close()
        return redirect('/reservations')
    
    cursor.execute("""
        INSERT INTO Reservation (Customer_customer_id, DiningTable_table_id, reservation_date, party_size)
        VALUES (%s, %s, %s, %s)
    """, (customer_id, table_id, reservation_date, party_size))
    conn.commit()
    conn.close()
    flash("Reservation added successfully!")
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

    # Get the reservation with customer info and table
    cursor.execute("""
        SELECT r.reservation_id, r.Customer_customer_id, r.DiningTable_table_id, r.reservation_date, r.party_size,
            c.first_name, c.last_name, t.capacity as table_capacity
        FROM reservation r
        JOIN customer c ON r.Customer_customer_id = c.customer_id
        JOIN DiningTable t ON r.DiningTable_table_id = t.table_id
        WHERE r.reservation_id = %s
    """, (id,))
    reservation = cursor.fetchone()

    if reservation is None:
        flash("Reservation not found.")
        conn.close()
        return redirect("/reservations")

    if request.method == "POST":
        reservation_date = request.form.get("reservation_date")
        party_size = request.form.get("party_size")

        errors = []

        # Validate reservation date
        if not reservation_date:
            errors.append("Reservation date is required.")
        else:
            from datetime import datetime, date
            try:
                res_date = datetime.strptime(reservation_date, "%Y-%m-%d").date()
                if res_date < date.today():
                    errors.append("Reservation date cannot be in the past.")
            except ValueError:
                errors.append("Invalid date format. Use YYYY-MM-DD.")

        # Validate party size
        if not party_size:
            errors.append("Party size is required.")
        else:
            try:
                party_size_int = int(party_size)
                if party_size_int <= 0:
                    errors.append("Party size must be greater than 0.")
                elif party_size_int > 15:
                    errors.append("Party size must be at most 15.")
                elif party_size_int > reservation['table_capacity']:
                    errors.append(f"Party size cannot exceed table capacity ({reservation['table_capacity']}).")
            except ValueError:
                errors.append("Party size must be a number.")

        if errors:
            for error in errors:
                flash(error)
            return render_template("update_reservation.html", reservation=reservation)

        # Update reservation if valid
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


# ORDERS

@app.route("/orders")
def orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all orders with customer and employee names, include customer_id
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.status,
            c.customer_id, c.first_name, c.last_name,
            e.first_name AS emp_first_name, e.last_name AS emp_last_name
        FROM `Order` o
        JOIN Customer c ON o.Customer_customer_id = c.customer_id
        JOIN Employee e ON o.Employee_employee_id = e.employee_id
        ORDER BY o.order_date DESC
    """)
    orders = cursor.fetchall()

    # Get all customers for dropdown
    cursor.execute("SELECT customer_id, first_name, last_name FROM Customer")
    customers = cursor.fetchall()

    # Get all employees who are servers only
    cursor.execute("SELECT employee_id, first_name, last_name FROM Employee WHERE role = 'Server'")
    employees = cursor.fetchall()

    conn.close()
    return render_template("orders.html", orders=orders, customers=customers, employees=employees)

from datetime import datetime

@app.route("/add_order", methods=["POST"])
def add_order():
    customer_id = request.form.get("customer_id")
    employee_id = request.form.get("employee_id")
    order_date = request.form.get("order_date")
    status = request.form.get("status") or "Pending"

    errors = []

    if not customer_id:
        errors.append("Please select a customer.")
    if not employee_id:
        errors.append("Please select an employee.")
    
    # Validate order_date
    if not order_date:
        errors.append("Please select an order date.")
    else:
        try:
            order_date_obj = datetime.strptime(order_date, "%Y-%m-%dT%H:%M")
        except ValueError:
            errors.append("Invalid order date format.")

    if errors:
        for e in errors:
            flash(e)
        return redirect("/orders")

    # All good → insert into DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO `Order` (Customer_customer_id, Employee_employee_id, order_date, status)
        VALUES (%s, %s, %s, %s)
    """, (customer_id, employee_id, order_date_obj, status))
    conn.commit()
    conn.close()
    flash("Order added successfully!")
    return redirect("/orders")



@app.route("/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Delete related order items first
    cursor.execute("DELETE FROM OrderItem WHERE Order_order_id = %s", (order_id,))
    cursor.execute("DELETE FROM `Order` WHERE order_id = %s", (order_id,))
    conn.commit()
    conn.close()
    flash("Order deleted successfully!")
    return redirect("/orders")

from datetime import datetime

@app.route("/update_order/<int:order_id>", methods=["GET", "POST"])
def update_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM `Order` WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        flash("Order not found")
        conn.close()
        return redirect("/orders")

    if request.method == "POST":
        status = request.form.get("status")
        order_date_input = request.form.get("order_date")

        errors = []

        # Validate date
        if not order_date_input:
            errors.append("Order date is required.")
        else:
            try:
                # Parse string from form
                order_date_obj = datetime.strptime(order_date_input, "%Y-%m-%dT%H:%M")
            except ValueError:
                errors.append("Invalid date format.")

        if errors:
            for e in errors:
                flash(e)
            return render_template("update_order.html", order=order)

        # Update DB
        cursor.execute("""
            UPDATE `Order`
            SET order_date=%s, status=%s
            WHERE order_id=%s
        """, (order_date_obj, status, order_id))

        conn.commit()
        conn.close()
        flash("Order updated successfully!")
        return redirect("/orders")

    # Convert datetime → string for HTML input
    if order["order_date"]:
        order["order_date"] = order["order_date"].strftime("%Y-%m-%dT%H:%M")

    conn.close()
    return render_template("update_order.html", order=order)


# ORDER ITEMS

# ------------------------
# ORDER ITEMS ROUTES
# ------------------------

@app.route('/order_items/<int:order_id>')
def order_items(order_id):
    """Show all items for a specific order"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch order info
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.status, c.first_name, c.last_name
        FROM `Order` o
        JOIN Customer c ON o.Customer_customer_id = c.customer_id
        WHERE o.order_id = %s
    """, (order_id,))
    order = cursor.fetchone()

    # Fetch items for the order
    cursor.execute("""
        SELECT oi.order_item_id, oi.quantity, oi.special_instructions, 
            m.name AS menu_item_name, m.Price
        FROM OrderItem oi
        JOIN MenuItem m ON oi.MenuItem_menu_item_id = m.menu_item_id
        WHERE oi.Order_order_id = %s
    """, (order_id,))
    items = cursor.fetchall()

    # Fetch all menu items for adding new order items
    cursor.execute("SELECT menu_item_id, name, Price FROM MenuItem")
    menu_items = cursor.fetchall()

    conn.close()
    return render_template('order_items.html', order=order, items=items, menu_items=menu_items)


@app.route('/add_order_item', methods=['POST'])
def add_order_item():
    order_id = request.form['order_id']
    menu_item_id = request.form['menu_item_id']
    quantity = request.form['quantity']
    instructions = request.form.get('special_instructions', '')

    errors = []
    if not quantity.isdigit() or int(quantity) < 1:
        errors.append("Quantity must be a positive number.")

    if errors:
        for e in errors:
            flash(e)
        return redirect(f'/order_items/{order_id}')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO OrderItem (Order_order_id, MenuItem_menu_item_id, quantity, special_instructions)
        VALUES (%s, %s, %s, %s)
    """, (order_id, menu_item_id, quantity, instructions))
    conn.commit()
    conn.close()
    flash("Order item added successfully!")
    return redirect(f'/order_items/{order_id}')


@app.route('/update_order_item/<int:item_id>', methods=['POST'])
def update_order_item(item_id):
    quantity = request.form['quantity']
    instructions = request.form.get('special_instructions', '')

    if not quantity.isdigit() or int(quantity) < 1:
        flash("Quantity must be a positive number.")
        # Need to fetch order_id to redirect
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Order_order_id FROM OrderItem WHERE order_item_id = %s", (item_id,))
        order_id = cursor.fetchone()[0]
        conn.close()
        return redirect(f'/order_items/{order_id}')

    conn = get_db_connection()
    cursor = conn.cursor()
    # Get order_id for redirect
    cursor.execute("SELECT Order_order_id FROM OrderItem WHERE order_item_id = %s", (item_id,))
    order_id = cursor.fetchone()[0]

    cursor.execute("""
        UPDATE OrderItem
        SET quantity=%s, special_instructions=%s
        WHERE order_item_id=%s
    """, (quantity, instructions, item_id))
    conn.commit()
    conn.close()
    flash("Order item updated successfully!")
    return redirect(f'/order_items/{order_id}')


@app.route('/delete_order_item/<int:item_id>', methods=['POST'])
def delete_order_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get order_id for redirect
    cursor.execute("SELECT Order_order_id FROM OrderItem WHERE order_item_id = %s", (item_id,))
    order_id = cursor.fetchone()[0]

    cursor.execute("DELETE FROM OrderItem WHERE order_item_id = %s", (item_id,))
    conn.commit()
    conn.close()
    flash("Order item deleted successfully!")
    return redirect(f'/order_items/{order_id}')


@app.route("/customer/<int:customer_id>/summary")
def customer_summary(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all orders for this customer
    cursor.execute("SELECT order_id, order_date FROM `Order` WHERE Customer_customer_id = %s", (customer_id,))
    orders = cursor.fetchall()

    # Add total for each order using the MySQL function
    for order in orders:
        cursor.execute("SELECT GetOrderTotal(%s) AS total", (order['order_id'],))
        order_total = cursor.fetchone()
        order['total'] = float(order_total['total'])

    # Sum up all orders to get customer's total spent
    total_spent = sum(order['total'] for order in orders)

    conn.close()
    return render_template("customer_summary.html", orders=orders, total_spent=total_spent)

if __name__ == '__main__':
    app.run(debug=True)

