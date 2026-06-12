FROM openquantumsafe/python:latest

USER root

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py .

# Expose both potential host-facing ports
EXPOSE 8001
EXPOSE 8002

USER oqs

CMD ["python3", "app.py"]