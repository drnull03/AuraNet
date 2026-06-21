FROM postgres:15-alpine

# Set default credentials for the clinical database
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=clinical_secret_99
ENV POSTGRES_DB=vitalsync

# Any .sql file in this directory is automatically executed when the container starts
COPY init.sql /docker-entrypoint-initdb.d/

EXPOSE 5432
