-- Reset tables
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    ssn VARCHAR(11),
    balance DECIMAL(15,2),
    account_type VARCHAR(50)
);

CREATE TABLE loans (
    id VARCHAR(20) PRIMARY KEY,
    account_id INT,
    amount DECIMAL(15,2),
    status VARCHAR(50)
);

-- 25 Accounts
INSERT INTO accounts (customer_name, ssn, balance, account_type) VALUES
('John Doe', '111-22-1111', 24500.00, 'Checking'),
('Jane Smith', '111-22-2222', 142800.50, 'Investment'),
('Michael Chen', '111-22-3333', 3450.75, 'Savings'),
('Sarah Connor', '111-22-4444', 5500.00, 'Checking'),
('James Bond', '111-22-5555', 999999.00, 'Investment'),
('Alice Wonderland', '111-22-6666', 1200.00, 'Savings'),
('Bob Builder', '111-22-7777', 8500.00, 'Checking'),
('Charlie Brown', '111-22-8888', 400.25, 'Savings'),
('Diana Prince', '111-22-9999', 75000.00, 'Investment'),
('Edward Norton', '111-22-0001', 3200.00, 'Checking'),
('Fiona Apple', '111-22-0002', 150.50, 'Savings'),
('George Costanza', '111-22-0003', 25.00, 'Checking'),
('Hannah Abbott', '111-22-0004', 6000.00, 'Savings'),
('Ian Malcolm', '111-22-0005', 45000.00, 'Investment'),
('Jack Sparrow', '111-22-0006', 0.01, 'Checking'),
('Kelly Kapowski', '111-22-0007', 9500.00, 'Savings'),
('Liam Neeson', '111-22-0008', 22000.00, 'Investment'),
('Mona Lisa', '111-22-0009', 1000000.00, 'Master Account'),
('Nancy Drew', '111-22-0010', 4000.00, 'Savings'),
('Oscar Isaac', '111-22-0011', 12000.00, 'Checking'),
('Peter Parker', '111-22-0012', 300.00, 'Savings'),
('Quinn Fabray', '111-22-0013', 2500.00, 'Checking'),
('Riley Reid', '111-22-0014', 55000.00, 'Investment'),
('Steve Rogers', '111-22-0015', 7000.00, 'Savings'),
('Admin User', '999-99-9999', 9999999.99, 'Master Account');

-- 25 Loans
INSERT INTO loans (id, account_id, amount, status) VALUES
('L-101', 1, 5000.00, 'Approved'), ('L-102', 2, 25000.00, 'Approved'),
('L-103', 3, 1500.00, 'Pending'), ('L-104', 4, 3000.00, 'Approved'),
('L-105', 5, 50000.00, 'Approved'), ('L-106', 6, 500.00, 'Rejected'),
('L-107', 7, 2000.00, 'Approved'), ('L-108', 8, 800.00, 'Pending'),
('L-109', 9, 15000.00, 'Approved'), ('L-110', 10, 1000.00, 'Approved'),
('L-111', 11, 200.00, 'Pending'), ('L-112', 12, 100.00, 'Approved'),
('L-113', 13, 3000.00, 'Approved'), ('L-114', 14, 25000.00, 'Approved'),
('L-115', 15, 50.00, 'Rejected'), ('L-116', 16, 4000.00, 'Approved'),
('L-117', 17, 12000.00, 'Approved'), ('L-118', 18, 500000.00, 'Approved'),
('L-119', 19, 2000.00, 'Pending'), ('L-120', 20, 6000.00, 'Approved'),
('L-121', 21, 500.00, 'Approved'), ('L-122', 22, 1200.00, 'Approved'),
('L-123', 23, 25000.00, 'Approved'), ('L-124', 24, 3500.00, 'Pending'),
('L-125', 25, 999999.00, 'Approved');