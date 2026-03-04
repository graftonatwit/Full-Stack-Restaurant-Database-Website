from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@flag961TOAD",
        database="myrestaurantdb"
    )

# Home page
@app.route('/')
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

    #cursor.execute("DELETE FROM OrderItem WHERE customer_id = %s", (customer_id,))
    cursor.execute("DELETE FROM Customer WHERE customer_id = %s", (customer_id,))

    conn.commit()
    conn.close()

    return redirect("/customers")
if __name__ == '__main__':
    app.run(debug=True)
