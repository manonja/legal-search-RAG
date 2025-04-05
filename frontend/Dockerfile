# syntax=docker/dockerfile:1

FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Build the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects anonymous telemetry data
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV PORT=8080
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_SENTRY_DSN=""
ENV NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_TOKEN=""
ENV NEXT_PUBLIC_ADMIN_PASSWORD=""
ENV NEXT_PUBLIC_USER_PASSWORD=""
ENV NEXT_PUBLIC_FIREBASE_API_KEY=""
ENV NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=""
ENV NEXT_PUBLIC_FIREBASE_PROJECT_ID=""
ENV NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=""
ENV NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=""
ENV NEXT_PUBLIC_FIREBASE_APP_ID=""


# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install Sharp for image optimization in standalone mode
RUN npm install --platform=linux --arch=x64 sharp

# Copy necessary files from build stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/package.json ./package.json

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Expose the port
EXPOSE 8080

# Start the application with proper environment variables
CMD ["node", "server.js"]
