# Dockerfile
FROM node:20-alpine


WORKDIR /usr/src/app


COPY package*.json ./


RUN npm install --omit=dev


COPY . .


USER node


CMD ["node", "index.js"]