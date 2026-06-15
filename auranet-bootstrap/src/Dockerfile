FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY index.js .

# The application executes immediately upon container start
ENTRYPOINT ["node", "index.js"]