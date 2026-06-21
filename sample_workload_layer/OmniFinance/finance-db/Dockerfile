FROM postgres:15-alpine

# Set default credentials (can be overridden by K8s later)
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=supersecret
ENV POSTGRES_DB=omnifinance

# Any .sql file in this directory is automatically executed when the container starts for the first time
COPY init.sql /docker-entrypoint-initdb.d/
