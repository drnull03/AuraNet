FROM python:3.10-slim

WORKDIR /app

# Install libbpf required for pure-python RingBuffer access
RUN apt-get update && apt-get install -y libbpf0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY forwarder.py .
RUN chmod +x forwarder.py

CMD ["python", "forwarder.py"]