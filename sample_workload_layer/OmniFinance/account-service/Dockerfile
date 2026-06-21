FROM python:3.10-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app.py .

# Expose the port the Flask app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
