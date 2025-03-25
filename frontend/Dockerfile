# Use Node.js 18 as the base image
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package.json (and package-lock.json if it exists)
COPY package.json ./

# Install dependencies with better error handling
RUN npm install --no-fund --no-audit || (echo "npm install failed, retrying..." && npm install --no-fund --no-audit)

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set the correct permissions
USER nextjs

# Expose port based on PORT env var with fallback to 3000
ENV PORT=${PORT:-3000}
EXPOSE ${PORT}

# Set the environment variable for the API URL, but allow it to be overridden
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://api:8000}

# Health check to ensure container is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/ || exit 1

# Start the application
CMD ["sh", "-c", "node server.js"]
