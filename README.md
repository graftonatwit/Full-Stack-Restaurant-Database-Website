MyRestaurant Database Overview

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

Face Recognition Login

The system includes a secure face recognition login for staff access:

Uses the user’s webcam in the browser to capture a live image.

Captured images are compared to a known staff face using the Python face_recognition library.

Upon successful recognition, the user is logged in and redirected to the homepage.

Provides a message (“Face recognized! You are logged in”) before automatically redirecting.

Prevents unauthorized access to the main application pages.

Technologies Used

Python

Flask

HTML

CSS

Jinja Templates

SQL Database (MySQL / SQLite depending on configuration)

JavaScript (for webcam capture)

face_recognition library for authentication

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

Relationships:

One customer can have multiple reservations:
Customer (1) ---- (Many) Reservation

How to Run the Project

Install Dependencies
Make sure Python and Flask are installed.

pip install flask face_recognition

Run the Flask Application

python app.py

Open the Website
Navigate to:

http://127.0.0.1:5000

Login with Face Recognition

The system will prompt for staff face scan before accessing the main application pages.

Main Pages

Home Page – Navigation to main parts of the application.

Add Customer – Form to add a new customer to the database.

Menu Page – Displays existing customers and allows updating or deleting them.

Reservation Page – Allows users to create reservations linked to a customer.

Future Improvements

Adding reservation editing functionality

Implementing authentication for multiple staff members

Improving UI styling

Adding validation for phone numbers and emails

Preventing duplicate reservations

Adding logging for login attempts

Author

Trevor Grafton
