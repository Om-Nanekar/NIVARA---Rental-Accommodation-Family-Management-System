USE rental_accommodation;

INSERT INTO rooms (room_number, floor, capacity, current_rent, status) VALUES
('101', 1, 4, 8500.00, 'OCCUPIED'),
('102', 1, 3, 7000.00, 'AVAILABLE'),
('201', 2, 5, 9500.00, 'AVAILABLE'),
('202', 2, 2, 6000.00, 'MAINTENANCE')
ON DUPLICATE KEY UPDATE room_number = VALUES(room_number);

INSERT INTO electricity_rates (rate_per_unit, effective_from, effective_to)
SELECT 8.50, '2026-01-01', NULL
WHERE NOT EXISTS (SELECT 1 FROM electricity_rates);

INSERT INTO system_settings (upi_id, upi_name, property_name, property_contact)
SELECT 'property@upi', 'Property Owner', 'Sunrise Rental Accommodation', '9876543210'
WHERE NOT EXISTS (SELECT 1 FROM system_settings);

INSERT INTO admin (username, password_hash)
SELECT 'admin', 'pbkdf2:sha256:600000$rentalDemoSalt$7aff374fffe95d0d8dc88f2e25c3f50b8a68364557229e35054547e16c82b471'
WHERE NOT EXISTS (SELECT 1 FROM admin WHERE username = 'admin');
