# customer-api/init_db.py
import sqlite3

def init_database():
    # Connect to the local SQLite database file
    conn = sqlite3.connect("bank_customers.db")
    cursor = conn.cursor()

    # Define the simplified schema with integer primary keys
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            account_type TEXT NOT NULL,
            kyc_status TEXT NOT NULL
        )
    """)

    # Clean the table for a fresh test run
    cursor.execute("DELETE FROM customers")

    # 25 Realistic, sequential banking profiles
    mock_customers = [
        (1, "Alice Vance", "alice.vance@example.com", "Retail-Checking", "Verified"),
        (2, "Bob Miller", "bob.miller@example.com", "Retail-Savings", "Verified"),
        (3, "Charlie Smith", "charlie.smith@example.com", "Retail-Checking", "Pending"),
        (4, "Diana Prince", "diana.prince@example.com", "Premium-Retail", "Verified"),
        (5, "Evan Wright", "evan.wright@example.com", "Retail-Checking", "Verified"),
        (6, "Fiona Gallagher", "fiona.g@example.com", "Retail-Savings", "Suspended"),
        (7, "George Brooks", "george.b@example.com", "Small-Business", "Verified"),
        (8, "Hannah Abbott", "hannah.a@example.com", "Premium-Retail", "Verified"),
        (9, "Ian Malcolm", "chaos@example.com", "Retail-Savings", "Pending"),
        (10, "Julia Roberts", "julia.r@example.com", "Wealth-Management", "Verified"),
        (11, "Kevin Mitnick", "kevin@example.com", "Retail-Checking", "Suspended"),
        (12, "Laura Croft", "laura@example.com", "Premium-Retail", "Verified"),
        (13, "Michael Scott", "michael@dundermifflin.com", "Small-Business", "Verified"),
        (14, "Nina Simone", "nina@example.com", "Retail-Savings", "Verified"),
        (15, "Oscar Martinez", "oscar@dundermifflin.com", "Retail-Checking", "Verified"),
        (16, "Penelope Cruz", "penelope@example.com", "Premium-Retail", "Pending"),
        (17, "Quinn Fabray", "quinn@example.com", "Retail-Savings", "Verified"),
        (18, "Raymond Reddington", "ray@example.com", "Wealth-Management", "Verified"),
        (19, "Sarah Connor", "sarah@skynet-resistance.org", "Retail-Checking", "Verified"),
        (20, "Thomas Anderson", "neo@matrix.io", "Retail-Savings", "Suspended"),
        (21, "Ursula Buffay", "ursula@example.com", "Retail-Checking", "Pending"),
        (22, "Victor Von Doom", "doom@latveria.gov", "Wealth-Management", "Verified"),
        (23, "Wendy Darling", "wendy@neverland.net", "Retail-Savings", "Verified"),
        (24, "Xavier Charles", "professorx@mutant.edu", "Small-Business", "Verified"),
        (25, "Youssef Hassan", "youssef.h@example.com", "Premium-Retail", "Verified")
    ]

    # Insert dataset into the local SQLite node
    cursor.executemany("""
        INSERT INTO customers (id, name, email, account_type, kyc_status)
        VALUES (?, ?, ?, ?, ?)
    """, mock_customers)

    conn.commit()
    conn.close()
    print("Successfully seeded 'bank_customers.db' with 25 simplified records.")

if __name__ == "__main__":
    init_database()