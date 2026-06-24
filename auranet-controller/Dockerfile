FROM python:3.10-slim

WORKDIR /app

# 1. Install CPU-only PyTorch explicitly to avoid the 5GB CUDA bloat
RUN pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu

# 2. Copy requirements and install the rest (Flower, Numpy)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the models and source code
COPY models/ /app/models/
COPY src/ /app/src/

EXPOSE 8080

CMD ["python", "src/server.py"]
