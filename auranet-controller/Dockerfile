FROM python:3.10-slim

WORKDIR /app

# Install dependencies first to cache the layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /app/src/

# Expose the gRPC port Flower uses to communicate with the Agents
EXPOSE 8080

# Run the central Flower server
CMD ["python", "src/server.py"]