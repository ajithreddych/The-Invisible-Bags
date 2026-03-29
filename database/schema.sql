-- schema.sql
-- Database: rice_mill_ai
-- Run this file using:
-- /usr/local/mysql/bin/mysql -u root -p rice_mill_ai < database/schema.sql

CREATE TABLE IF NOT EXISTS bills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_no VARCHAR(100) UNIQUE NOT NULL,
    farmer_id VARCHAR(100) NOT NULL,
    trader_id VARCHAR(100) NOT NULL,
    mill_id VARCHAR(100) NOT NULL,
    vehicle_no VARCHAR(50) NOT NULL,
    bill_date DATETIME NOT NULL,
    manual_bag_count INT NOT NULL,
    manual_total_weight FLOAT DEFAULT NULL,
    status ENUM('PENDING','VERIFIED','MISMATCH') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(100) UNIQUE NOT NULL,
    mill_id VARCHAR(100) NOT NULL,
    gate_id VARCHAR(100) NOT NULL,
    vehicle_no VARCHAR(50) NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME DEFAULT NULL,
    ai_bag_count INT NOT NULL,
    ai_est_weight FLOAT DEFAULT NULL,
    video_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reconciliation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    batch_id VARCHAR(100) NOT NULL,
    manual_bag_count INT NOT NULL,
    ai_bag_count INT NOT NULL,
    difference INT NOT NULL,
    result ENUM('MATCH','MISMATCH') NOT NULL,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    batch_id VARCHAR(100) NOT NULL,
    severity ENUM('LOW','MEDIUM','HIGH') DEFAULT 'LOW',
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
