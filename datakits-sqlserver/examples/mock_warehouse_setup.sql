-- Mock Warehouse Setup for Testing
-- =================================
-- This creates a simple test database with one table for demonstration

-- Create test database (run as admin)
CREATE DATABASE IF NOT EXISTS TestWarehouse;
USE TestWarehouse;

-- Create a simple Customer table
CREATE TABLE IF NOT EXISTS dbo.Customer (
    customer_id INT PRIMARY KEY,
    first_name NVARCHAR(50),
    last_name NVARCHAR(50),
    email NVARCHAR(100),
    phone NVARCHAR(20),
    address NVARCHAR(200),
    city NVARCHAR(50),
    state NVARCHAR(2),
    zip_code NVARCHAR(10),
    country NVARCHAR(50),
    created_date DATETIME DEFAULT GETDATE(),
    last_modified DATETIME DEFAULT GETDATE(),
    is_active BIT DEFAULT 1
);

-- Insert sample data
INSERT INTO dbo.Customer (customer_id, first_name, last_name, email, phone, address, city, state, zip_code, country)
VALUES
    (1, 'John', 'Doe', 'john.doe@example.com', '555-0101', '123 Main St', 'Seattle', 'WA', '98101', 'USA'),
    (2, 'Jane', 'Smith', 'jane.smith@example.com', '555-0102', '456 Oak Ave', 'Portland', 'OR', '97201', 'USA'),
    (3, 'Bob', 'Johnson', 'bob.johnson@example.com', '555-0103', '789 Pine Rd', 'San Francisco', 'CA', '94102', 'USA'),
    (4, 'Alice', 'Williams', 'alice.w@example.com', '555-0104', '321 Elm St', 'Los Angeles', 'CA', '90001', 'USA'),
    (5, 'Charlie', 'Brown', 'charlie.b@example.com', '555-0105', '654 Maple Dr', 'Denver', 'CO', '80201', 'USA'),
    (6, 'Diana', 'Davis', 'diana.d@example.com', '555-0106', '987 Cedar Ln', 'Phoenix', 'AZ', '85001', 'USA'),
    (7, 'Edward', 'Miller', 'edward.m@example.com', '555-0107', '147 Spruce Way', 'Austin', 'TX', '73301', 'USA'),
    (8, 'Fiona', 'Wilson', 'fiona.w@example.com', '555-0108', '258 Birch Blvd', 'Miami', 'FL', '33101', 'USA'),
    (9, 'George', 'Moore', 'george.m@example.com', '555-0109', '369 Willow Ct', 'Chicago', 'IL', '60601', 'USA'),
    (10, 'Helen', 'Taylor', 'helen.t@example.com', '555-0110', '741 Aspen Pl', 'Boston', 'MA', '02101', 'USA');

-- Create a view to verify data
CREATE VIEW CustomerSummary AS
SELECT
    COUNT(*) as total_customers,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_customers,
    MIN(created_date) as earliest_customer,
    MAX(created_date) as latest_customer
FROM dbo.Customer;

-- Grant permissions (adjust for your service account)
-- GRANT SELECT ON dbo.Customer TO [DOMAIN\svc_airflow];