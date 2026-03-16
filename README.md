MyRestaurant Database
Overview

The MyRestaurant Database is a web-based restaurant reservation management system built using Flask, Python, HTML, and a relational database. The application allows restaurant staff to manage customers and reservations through a simple web interface.

The system supports adding, viewing, updating, and deleting customer records, as well as creating and managing reservations linked to those customers.

Features
Customer Management

Users can:

Add new customers

View all customers in a table

Update customer information

Delete customer records

Customer information includes:

Customer ID

First Name

Last Name

Phone Number

Email Address

Reservation Management

Users can:

Create reservations

View all reservations

Delete reservations

Reservation information includes:

Reservation ID

Customer ID

Reservation Date

Party Size

Customer Name

Reservations are linked to customers through a foreign key relationship.

Technologies Used

Python

Flask

HTML

CSS

Jinja Templates

SQL Database (MySQL / SQLite depending on configuration)

Database Structure
Customer Table

Stores information about restaurant customers.

Fields:

customer_id (Primary Key)

first_name

last_name

phone_number

email

Reservation Table

Stores reservation details.

Fields:

reservation_id (Primary Key)

Customer_customer_id (Foreign Key referencing Customer)

reservation_date

party_size

Relationships

Customer → Reservation
One customer can have multiple reservations.

Relationship type:

Customer (1) ---- (Many) Reservation
How to Run the Project
1. Install Dependencies

Make sure Python and Flask are installed.

pip install flask
2. Run the Flask Application
python app.py
3. Open the Website

Navigate to:

http://127.0.0.1:5000
Main Pages

Home Page
Displays navigation to the main parts of the application.

Add Customer
Form to add a new customer to the database.

Menu Page
Displays existing customers and allows updating or deleting them.

Reservation Page
Allows users to create reservations linked to a customer.

Future Improvements

Potential improvements include:

Adding reservation editing functionality

Implementing authentication for staff access

Improving UI styling

Adding validation for phone numbers and emails

Preventing duplicate reservations

Author

Trevor Grafton
