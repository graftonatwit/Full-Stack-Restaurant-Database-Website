


-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema: restaurantdb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `restaurantdb` DEFAULT CHARACTER SET utf8;
USE `restaurantdb`;

-- -----------------------------------------------------
-- Table: Customer
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Customer` (
    customer_id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(45),
    last_name VARCHAR(45),
    phone_number VARCHAR(15),
    email VARCHAR(100),
    PRIMARY KEY (customer_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: Employee
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Employee` (
    employee_id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(45),
    last_name VARCHAR(45),
    role ENUM('Server', 'Chef', 'Host', 'Manager', 'Bartender'),
    hire_date DATE,
    PRIMARY KEY (employee_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: DiningTable
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `DiningTable` (
    table_id INT NOT NULL AUTO_INCREMENT,
    table_number INT,
    capacity INT,
    location VARCHAR(45),
    PRIMARY KEY (table_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: Reservation
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Reservation` (
    reservation_id INT NOT NULL AUTO_INCREMENT,
    reservation_date DATETIME,
    party_size INT,
    Customer_customer_id INT NOT NULL,
    DiningTable_table_id INT NOT NULL,
    PRIMARY KEY (reservation_id),
    FOREIGN KEY (Customer_customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (DiningTable_table_id) REFERENCES DiningTable(table_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: MenuItem
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `MenuItem` (
    menu_item_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100),
    description VARCHAR(255),
    price DECIMAL(6,2),
    PRIMARY KEY (menu_item_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: Category
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Category` (
    category_id INT NOT NULL AUTO_INCREMENT,
    category_name ENUM('Appetizer', 'Soup', 'Salad', 'Entree', 'Drink', 'Dessert'),
    PRIMARY KEY (category_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: MenuItemCategory (many-to-many)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `MenuItemCategory` (
    menu_item_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (menu_item_id, category_id),
    FOREIGN KEY (menu_item_id) REFERENCES MenuItem(menu_item_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: `Order`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Order` (
    order_id INT NOT NULL AUTO_INCREMENT,
    order_date DATETIME,
    status ENUM('Pending', 'In Progress', 'Completed', 'Cancelled'),
    Customer_customer_id INT NOT NULL,
    Employee_employee_id INT NOT NULL,
    PRIMARY KEY (order_id),
    FOREIGN KEY (Customer_customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (Employee_employee_id) REFERENCES Employee(employee_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- Table: OrderItem
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `OrderItem` (
    order_item_id INT NOT NULL AUTO_INCREMENT,
    quantity INT,
    special_instructions VARCHAR(255),
    Order_order_id INT NOT NULL,
    MenuItem_menu_item_id INT NOT NULL,
    PRIMARY KEY (order_item_id),
    FOREIGN KEY (Order_order_id) REFERENCES `Order`(order_id),
    FOREIGN KEY (MenuItem_menu_item_id) REFERENCES MenuItem(menu_item_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- VIEW: OrderSummary
-- -----------------------------------------------------
CREATE OR REPLACE VIEW OrderSummary AS
SELECT 
    o.order_id,
    c.first_name,
    c.last_name,
    o.order_date,
    SUM(oi.quantity * m.price) AS total_price
FROM `Order` o
JOIN Customer c ON o.Customer_customer_id = c.customer_id
JOIN OrderItem oi ON o.order_id = oi.Order_order_id
JOIN MenuItem m ON oi.MenuItem_menu_item_id = m.menu_item_id
GROUP BY o.order_id;

-- -----------------------------------------------------
-- PROCEDURE: CreateOrder
-- -----------------------------------------------------
DELIMITER $$
CREATE PROCEDURE CreateOrder (
    IN cust_id INT,
    IN emp_id INT
)
BEGIN
    INSERT INTO `Order` (order_date, status, Customer_customer_id, Employee_employee_id)
    VALUES (NOW(), 'Pending', cust_id, emp_id);
END $$
DELIMITER ;

-- -----------------------------------------------------
-- FUNCTION: GetOrderTotal
-- -----------------------------------------------------
DELIMITER $$
CREATE FUNCTION GetOrderTotal(orderId INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);

    SELECT SUM(oi.quantity * m.price)
    INTO total
    FROM OrderItem oi
    JOIN MenuItem m ON oi.MenuItem_menu_item_id = m.menu_item_id
    WHERE oi.Order_order_id = orderId;

    RETURN IFNULL(total, 0);
END $$
DELIMITER ;

-- -----------------------------------------------------
-- TRIGGER: Validate OrderItem Quantity
-- -----------------------------------------------------
DELIMITER $$
CREATE TRIGGER before_orderitem_insert
BEFORE INSERT ON OrderItem
FOR EACH ROW
BEGIN
    IF NEW.quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Quantity must be greater than 0';
    END IF;
END $$
DELIMITER ;

-- -----------------------------------------------------
-- REPORT: Top Customers by Spending
-- -----------------------------------------------------
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    SUM(oi.quantity * m.price) AS total_spent
FROM Customer c
JOIN `Order` o ON c.customer_id = o.Customer_customer_id
JOIN OrderItem oi ON o.order_id = oi.Order_order_id
JOIN MenuItem m ON oi.MenuItem_menu_item_id = m.menu_item_id
GROUP BY c.customer_id
ORDER BY total_spent DESC;