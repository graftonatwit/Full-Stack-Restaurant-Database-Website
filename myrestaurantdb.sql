-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema myRestaurantdb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema myRestaurantdb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `myRestaurantdb` DEFAULT CHARACTER SET utf8 ;
USE `myRestaurantdb` ;

-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Customer`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`Customer` (
  `customer_id` INT not Null AUTO_INCREMENT,
  `first_name` VARCHAR(45) NULL,
  `last_name` VARCHAR(45) NULL,
  `phone_number` VARCHAR(15) NULL,
  `email` VARCHAR(100) NULL,
  PRIMARY KEY (`customer_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Reservation`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`Reservation` (
  `reservation_id` INT NOT NULL AUTO_INCREMENT,
  `reservation_date` DATETIME NULL,
  `party_size` INT NULL,
  `Customer_customer_id` INT NOT NULL,
  PRIMARY KEY (`reservation_id`),
  INDEX `fk_Reservation_Customer_idx` (`Customer_customer_id` ASC) VISIBLE,
  CONSTRAINT `fk_Reservation_Customer`
    FOREIGN KEY (`Customer_customer_id`)
    REFERENCES `myRestaurantdb`.`Customer` (`customer_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Dining Table`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`DiningTable` (
  `table_id` INT NOT NULL AUTO_INCREMENT,
  `table_number` INT NULL,
  `capacity` INT NULL,
  `location` VARCHAR(45) NULL,
  `Reservation_reservation_id` INT NOT NULL,
  PRIMARY KEY (`table_id`),
  INDEX `fk_Dining Table_Reservation1_idx` (`Reservation_reservation_id` ASC) VISIBLE,
  CONSTRAINT `fk_Dining Table_Reservation1`
    FOREIGN KEY (`Reservation_reservation_id`)
    REFERENCES `myRestaurantdb`.`Reservation` (`reservation_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Employee`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`Employee` (
  `employee_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(45) NULL,
  `last_name` VARCHAR(45) NULL,
  `role` ENUM('Server', 'Chef', 'Host', 'Manager', 'Bartender') NULL,
  `hire_date` DATE NULL,
  PRIMARY KEY (`employee_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Order`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`Order` (
  `order_id` INT NOT NULL AUTO_INCREMENT,
  `order_date` DATETIME NULL,
  `status` ENUM('Pending', 'In Progress', 'Completed', 'Cancelled') NULL,
  `Customer_customer_id` INT NOT NULL,
  `Employee_employee_id` INT NOT NULL,
  PRIMARY KEY (`order_id`),
  INDEX `fk_Order_Customer1_idx` (`Customer_customer_id` ASC) VISIBLE,
  INDEX `fk_Order_Employee1_idx` (`Employee_employee_id` ASC) VISIBLE,
  CONSTRAINT `fk_Order_Customer1`
    FOREIGN KEY (`Customer_customer_id`)
    REFERENCES `myRestaurantdb`.`Customer` (`customer_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Order_Employee1`
    FOREIGN KEY (`Employee_employee_id`)
    REFERENCES `myRestaurantdb`.`Employee` (`employee_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`MenuItem`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`MenuItem` (
  `menu_item_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NULL,
  `description` VARCHAR(255) NULL,
  `Price` DECIMAL(6,2) NULL,
  PRIMARY KEY (`menu_item_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`Category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`Category` (
  `category_id` INT NOT NULL AUTO_INCREMENT,
  `category_name` ENUM('Appetizer', 'Soup', 'Salad', 'Entree', 'Drink', 'Dessert') NULL,
  `MenuItem_menu_item_id` INT NOT NULL,
  PRIMARY KEY (`category_id`),
  INDEX `fk_Category_MenuItem1_idx` (`MenuItem_menu_item_id` ASC) VISIBLE,
  CONSTRAINT `fk_Category_MenuItem1`
    FOREIGN KEY (`MenuItem_menu_item_id`)
    REFERENCES `myRestaurantdb`.`MenuItem` (`menu_item_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `myRestaurantdb`.`OrderItem`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `myRestaurantdb`.`OrderItem` (
  `order_item_id` INT NOT NULL AUTO_INCREMENT,
  `quantity` INT NULL,
  `special_instructions` VARCHAR(255) NULL,
  `Order_order_id` INT NOT NULL,
  PRIMARY KEY (`order_item_id`),
  INDEX `fk_OrderItem_Order1_idx` (`Order_order_id` ASC) VISIBLE,
  CONSTRAINT `fk_OrderItem_Order1`
    FOREIGN KEY (`Order_order_id`)
    REFERENCES `myRestaurantdb`.`Order` (`order_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
