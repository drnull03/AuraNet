-- Create the Accounts Table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    ssn VARCHAR(11),
    balance DECIMAL(15,2),
    account_type VARCHAR(50)
);

-- Insert dummy data for the SQL Injection demo
INSERT INTO accounts (customer_name, ssn, balance, account_type) VALUES
('John Doe', '***-**-1234', 24500.00, 'Checking'),
('Jane Smith', '***-**-5678', 142800.50, 'Investment'),
('Michael Chen', '***-**-9012', 3450.75, 'Savings'),
('Admin User', '***-**-9999', 9999999.99, 'Master Account');

-- Create the Loans Table
CREATE TABLE loans (
    id VARCHAR(20) PRIMARY KEY,
    account_id INT,
    amount DECIMAL(15,2),
    status VARCHAR(50)
);
--Insert dummy data for the SSRF demo
INSERT INTO loans (id, account_id, amount, status) VALUES
('L-901', 1, 350000.00, 'Approved'),
('L-902', 2, 15000.00, 'Pending Processing');
