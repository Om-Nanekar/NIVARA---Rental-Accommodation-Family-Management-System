CREATE DATABASE IF NOT EXISTS rental_accommodation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rental_accommodation;

CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    floor INT NOT NULL,
    capacity INT NOT NULL,
    current_rent DECIMAL(10,2) NOT NULL,
    status ENUM('AVAILABLE','OCCUPIED','MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE',
    INDEX idx_rooms_status (status),
    INDEX idx_rooms_floor (floor)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS families (
    family_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    head_name VARCHAR(100) NOT NULL,
    head_phone VARCHAR(15) NOT NULL,
    move_in_date DATE NOT NULL,
    move_out_date DATE NULL,
    status ENUM('ACTIVE','CHECKED_OUT') NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT fk_families_room FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    INDEX idx_families_room_status (room_id, status),
    INDEX idx_families_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS family_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    relationship_to_head VARCHAR(50) NOT NULL DEFAULT 'Member',
    CONSTRAINT fk_family_members_family FOREIGN KEY (family_id) REFERENCES families(family_id) ON DELETE CASCADE,
    INDEX idx_family_members_family (family_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS electricity_rates (
    rate_id INT AUTO_INCREMENT PRIMARY KEY,
    rate_per_unit DECIMAL(6,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    INDEX idx_electricity_rates_effective (effective_from, effective_to)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS electricity_readings (
    reading_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    reading_date DATE NOT NULL,
    previous_reading DECIMAL(10,2) NOT NULL,
    current_reading DECIMAL(10,2) NOT NULL,
    units_consumed DECIMAL(10,2) GENERATED ALWAYS AS (current_reading - previous_reading) STORED,
    CONSTRAINT fk_readings_room FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    CONSTRAINT chk_reading_progress CHECK (current_reading >= previous_reading),
    INDEX idx_readings_room_date (room_id, reading_date),
    UNIQUE KEY uq_reading_room_date (room_id, reading_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    room_id INT NOT NULL,
    reading_id INT NOT NULL,
    billing_month VARCHAR(7) NOT NULL,
    rent_amount DECIMAL(10,2) NOT NULL,
    units_consumed DECIMAL(10,2) NOT NULL,
    electricity_rate DECIMAL(6,2) NOT NULL,
    electricity_amount DECIMAL(10,2) NOT NULL,
    other_charges DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_payable DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    payment_status ENUM('UNPAID','PARTIALLY_PAID','PAID') NOT NULL DEFAULT 'UNPAID',
    CONSTRAINT fk_bills_family FOREIGN KEY (family_id) REFERENCES families(family_id),
    CONSTRAINT fk_bills_room FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    CONSTRAINT fk_bills_reading FOREIGN KEY (reading_id) REFERENCES electricity_readings(reading_id),
    INDEX idx_bills_family_month (family_id, billing_month),
    INDEX idx_bills_status_due (payment_status, due_date),
    UNIQUE KEY uq_bill_family_month (family_id, billing_month)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    payment_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_method ENUM('UPI','CASH','BANK_TRANSFER') NOT NULL,
    transaction_ref VARCHAR(100) NULL,
    CONSTRAINT fk_payments_bill FOREIGN KEY (bill_id) REFERENCES bills(bill_id),
    CONSTRAINT chk_payment_positive CHECK (amount_paid > 0),
    INDEX idx_payments_bill_date (bill_id, payment_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS system_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    upi_id VARCHAR(100) NOT NULL,
    upi_name VARCHAR(100) NOT NULL,
    property_name VARCHAR(150) NOT NULL,
    property_contact VARCHAR(15) NOT NULL
) ENGINE=InnoDB;
