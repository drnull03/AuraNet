# Start with a lightweight Python base
FROM python:3.10-slim

# Set the working directory
WORKDIR /app


COPY bin/hubble /usr/local/bin/hubble


RUN chmod +x /usr/local/bin/hubble

# Intall CPU-only PyTorch to keep the image size drastically smaller

RUN pip install --no-cache-dir torch==2.0.1 --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install the remaining dependencies (Flower, Numpy, NATS)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy the engine source code
COPY src/ /app/src/

# 6. Start the Master Orchestrator
CMD ["python", "src/engine.py"]