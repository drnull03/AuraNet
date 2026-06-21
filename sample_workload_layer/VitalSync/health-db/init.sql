-- Create the Patients Table (Highly Sensitive PHI)
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    dob DATE,
    ssn VARCHAR(11),
    blood_type VARCHAR(5)
);

-- Insert dummy data (Notice "John_Doe" matches our RCE test case)
INSERT INTO patients (full_name, dob, ssn, blood_type) VALUES
('John_Doe', '1985-04-12', '***-**-1111', 'O+'),
('Jane_Smith', '1990-08-24', '***-**-2222', 'A-'),
('Robert_Chen', '1978-11-05', '***-**-3333', 'B+');

-- Create the Medical Records Table
CREATE TABLE clinical_notes (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id),
    diagnosis TEXT,
    prescription TEXT,
    visit_date DATE
);

-- Insert dummy medical notes
INSERT INTO clinical_notes (patient_id, diagnosis, prescription, visit_date) VALUES
(1, 'Mild hypertension, advised dietary changes.', 'Lisinopril 10mg', '2023-10-01'),
(2, 'Routine physical exam. All vitals normal.', 'None', '2023-10-15'),
(3, 'Type 2 Diabetes management.', 'Metformin 500mg', '2023-10-20');
