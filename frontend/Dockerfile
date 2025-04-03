# Use Node.js 18 as the base image
FROM node:18-alpine AS base

# Build arguments that can be set during build
ARG VERSION_ARG=0.1.0
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG SENTRY_DSN
ARG ADMIN_PASSWORD
ARG USER_PASSWORD
ARG API_TOKEN

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

# Set environment variables for build time
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_VERSION=${VERSION_ARG}
ENV SENTRY_DSN=${SENTRY_DSN}
ENV NEXT_PUBLIC_API_TOKEN=${API_TOKEN}

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_VERSION=${VERSION_ARG}
ENV SENTRY_DSN=${SENTRY_DSN}
ENV ADMIN_PASSWORD=${ADMIN_PASSWORD}
ENV USER_PASSWORD=${USER_PASSWORD}
ENV API_TOKEN=${API_TOKEN}
ENV NEXT_PUBLIC_API_TOKEN=${API_TOKEN}

# Create a non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install sharp for image optimization in standalone mode
RUN npm install --no-fund --no-audit sharp

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set the correct permissions
USER nextjs

# Use port 10000 to match Render's default expectation
ENV PORT=10000
EXPOSE 10000

# Health check to ensure container is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:10000/ || exit 1

# Start the application
CMD ["sh", "-c", "node server.js"]
