# customer-api/main.py
import sqlite3
from fastapi import FastAPI, HTTPException

app = FastAPI(title="AuraNet Customer Core API", version="1.0.0")

def get_db_connection():
    conn = sqlite3.connect("bank_customers.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "customer-api"}

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):  # Type-hint changed to int for simpler ID matching
    """Fetches a specific customer profile using simplified integer IDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail=f"Customer record #{customer_id} not found.")
        
    return {
        "customer_id": row["id"],
        "full_name": row["name"],
        "email_address": row["email"],
        "tier": row["account_type"],
        "kyc_compliance": row["kyc_status"]
    }