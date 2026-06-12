# ~/AuraNet/sample_workload_layer/sample1/customer-api/Dockerfile

# Use a lightweight official Python runtime base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the dependency list first to leverage Docker caching layers
COPY requirements.txt .

# Install dependencies without saving local caches
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code and seed script
COPY main.py .
COPY init_db.py .

# Run the seeding script during the build process to pre-populate the bank_customers.db
RUN python init_db.py

# Expose the internal port FastAPI runs on
EXPOSE 8000

# Start the application using Uvicorn bound to all interfaces
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]