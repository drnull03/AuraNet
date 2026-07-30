# ==========================================
# Stage 1: Build the Application
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install all dependencies (including devDependencies needed for Vite/esbuild)
COPY package*.json ./
RUN npm ci

# Copy the rest of the source code
COPY . .

# Compile the React frontend to /dist/client 
# and the Node.js backend to /dist/server.cjs
RUN npm run build

# ==========================================
# Stage 2: Production Runtime Environment
# ==========================================
FROM node:20-alpine

WORKDIR /app

# Copy package.json to install only production dependencies
COPY package*.json ./
RUN npm ci --omit=dev

# Copy the compiled assets from the builder stage
COPY --from=builder /app/dist ./dist

# Set the default K8s networking and environment variables
ENV NATS_URL="nats://auranet-nats-broker.auranet-messaging.svc.cluster.local:4222"
ENV NODE_ENV="production"
ENV PORT=3000

# Expose the Express port
EXPOSE 3000

# Start the compiled Node.js backend
CMD ["npm", "start"]