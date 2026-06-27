FROM node:18-slim

WORKDIR /app

# Copy package files and install dependencies
COPY ./src/package*.json ./
RUN npm install --production

# Copy the forwarder script
COPY ./src/index.js .

# We don't expose any ports because this service only tails a local file and pushes outbound to NATS
CMD ["npm", "start"]