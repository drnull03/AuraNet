FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --production

# Changed from COPY index.js . to copy all .js files
COPY *.js ./

# We leave the ENTRYPOINT blank so we can override it in Helm depending on the Job!

COPY policies/ ./policies/