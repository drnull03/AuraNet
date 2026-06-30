import os
import base64
import requests
from flask import Flask, request, render_template_string, redirect, url_for
import oqs
import pyaes

app = Flask(__name__)

# Read configuration from environment variables
NODE_NAME = os.environ.get('NODE_NAME', 'Local Node')
PORT = int(os.environ.get('PORT', 5000))
TARGET_URL = os.environ.get('TARGET_URL', 'http://localhost:5001')

# Initialize Post-Quantum KEM (Kyber/ML-KEM)
KEM_ALGO = "Kyber768"
kem = oqs.KeyEncapsulation(KEM_ALGO)
public_key = kem.generate_keypair()

messages = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ node_name }}</title>
    <style>
        body { background: #11111b; color: #cdd6f4; font-family: monospace; padding: 2rem; }
        h1 { color: #cba6f7; border-bottom: 2px solid #313244; padding-bottom: 10px; }
        .info { color: #a6adc8; margin-bottom: 2rem; font-size: 0.9rem; }
        .highlight { color: #89b4fa; }
        .msg { background: #1e1e2e; border-left: 4px solid #a6e3a1; padding: 1rem; margin: 1rem 0; }
        .btn { background: #89b4fa; color: #11111b; padding: 10px 20px; border: none; font-weight: bold; cursor: pointer; }
        .btn:hover { background: #b4befe; }
    </style>
</head>
<body>
    <h1>[{{ node_name }}] running on port {{ port }}</h1>
    <div class="info">
        <p>Target Node URL: <span class="highlight">{{ target_url }}</span></p>
        <p>Algorithm: <span class="highlight">{{ kem_algo }} + Pure-Python AES-CTR</span></p>
    </div>

    <form action="/send" method="post">
        <button class="btn" type="submit">Send "Hello Post Quantum ERA"</button>
    </form>

    <h2>Decrypted Messages:</h2>
    {% if messages %}
        {% for msg in messages %}
            <div class="msg">> {{ msg }}</div>
        {% endfor %}
    {% else %}
        <p style="color: #585b70;">No messages received yet.</p>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, node_name=NODE_NAME, port=PORT, target_url=TARGET_URL, kem_algo=KEM_ALGO, messages=messages)

@app.route('/public-key', methods=['GET'])
def get_pk():
    return {'pk': base64.b64encode(public_key).decode('utf-8')}

@app.route('/send', methods=['POST'])
def send_message():
    try:
        # 1. Get Target's Public Key
        resp = requests.get(f"{TARGET_URL}/public-key", timeout=2)
        target_pk = base64.b64decode(resp.json()['pk'])

        # 2. Encapsulate a shared secret using Post-Quantum Math
        with oqs.KeyEncapsulation(KEM_ALGO) as sender_kem:
            kem_ciphertext, shared_secret = sender_kem.encap_secret(target_pk)

        # 3. Encrypt the actual message using Pure-Python AES
        iv = os.urandom(16)
        counter = pyaes.Counter(int.from_bytes(iv, byteorder='big'))
        aes = pyaes.AESModeOfOperationCTR(shared_secret[:32], counter=counter)
        
        plaintext = b"Hello Post Quantum ERA"
        msg_ciphertext = aes.encrypt(plaintext)

        payload = {
            'kem_ciphertext': base64.b64encode(kem_ciphertext).decode('utf-8'),
            'msg_iv': base64.b64encode(iv).decode('utf-8'),
            'msg_ciphertext': base64.b64encode(msg_ciphertext).decode('utf-8')
        }
        requests.post(f"{TARGET_URL}/receive", json=payload, timeout=2)
    except Exception as e:
        print(f"Error sending payload: {e}")
    return redirect(url_for('index'))

@app.route('/receive', methods=['POST'])
def receive():
    data = request.json
    kem_ciphertext = base64.b64decode(data['kem_ciphertext'])
    iv = base64.b64decode(data['msg_iv'])
    msg_ciphertext = base64.b64decode(data['msg_ciphertext'])

    # 1. Decapsulate the PQC cipher to retrieve the shared secret
    shared_secret = kem.decap_secret(kem_ciphertext)
    
    # 2. Use the shared secret to decrypt the AES payload
    counter = pyaes.Counter(int.from_bytes(iv, byteorder='big'))
    aes = pyaes.AESModeOfOperationCTR(shared_secret[:32], counter=counter)
    
    try:
        plaintext = aes.decrypt(msg_ciphertext)
        messages.append(plaintext.decode('utf-8'))
    except Exception as e:
        messages.append(f"Decryption failed: {str(e)}")
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)