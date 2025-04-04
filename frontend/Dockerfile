# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Copy necessary files from build stage
COPY --from=build /app/next.config.js ./
COPY --from=build /app/public ./public
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

# Create a health check endpoint for Cloud Run
RUN mkdir -p ./pages/api
RUN echo 'export default function handler(req, res) { res.status(200).json({ status: "ok" }) }' > ./pages/api/health.js

# User for running the application
USER node

# Expose the port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
