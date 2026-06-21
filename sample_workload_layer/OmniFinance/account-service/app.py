from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os

app = Flask(__name__)
# Enable CORS so the React frontend can talk to it later
CORS(app)

# Database connection configuration (Defaults to localhost for local testing)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASSWORD', 'supersecret')
DB_NAME = os.environ.get('DB_NAME', 'omnifinance')

def get_db_connection():
    return psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)

@app.route('/api/accounts', methods=['GET'])
def get_account():
    # Grab the ?id= parameter from the URL
    account_id = request.args.get('id')
    if not account_id:
        return jsonify({"error": "Missing account ID"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 🚨 INTENTIONAL VULNERABILITY: SQL INJECTION 🚨
        # We are putting the raw account_id directly into the query string.
        # If someone types "1 OR 1=1", it will become part of the SQL command!
        query = f"SELECT id, customer_name, ssn, balance, account_type FROM accounts WHERE id = {account_id}"
        print(f"[Account Service] Executing Query: {query}")
        
        cur.execute(query)
        rows = cur.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "customer_name": row[1],
                "ssn": row[2],
                "balance": float(row[3]),
                "account_type": row[4]
            })
            
        cur.close()
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        print(f"[Account Service] DB Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Account Service Online"}), 200

if __name__ == '__main__':
    # Listen on port 5000
    app.run(host='0.0.0.0', port=5000)