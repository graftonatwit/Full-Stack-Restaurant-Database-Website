
import os

from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime
from flask import Flask, render_template, redirect, session
from face_auth import authenticate_user
from PIL import Image
import io
import numpy as np
import face_recognition

app = Flask(__name__)
app.secret_key = "supersecretkey" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_FACE_PATH = os.path.join("static", "my_face.jpeg")

# Load known face encoding once at startup
known_image = face_recognition.load_image_file(KNOWN_FACE_PATH)
known_encodings = face_recognition.face_encodings(known_image)
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
                    <h2>Face recognized! You are logged in.</h2>
                    <p>Redirecting to homepage in 3 seconds...</p>
                    <script>
                        setTimeout(() => { window.location.href = '/'; }, 3000);
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

        cursor.execute("""
            UPDATE customer
            SET first_name=%s,
                last_name=%s,
                phone_number=%s,
                email=%s
            WHERE customer_id=%s
        """, (first, last, phone, email, id))

        conn.commit()

        return redirect("/customers")

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

    return redirect("/reservations")




if __name__ == '__main__':
    app.run(debug=True)
