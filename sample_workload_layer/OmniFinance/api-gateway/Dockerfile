FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --production

# Copy the gateway logic
COPY index.js .

EXPOSE 8080

CMD ["node", "index.js"]
