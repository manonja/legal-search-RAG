# Use Node.js LTS
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install --no-fund --no-audit

# Copy the rest of the application
COPY . .

# Build the Next.js app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Expose the port the app will run on
ENV PORT=3000
EXPOSE 3000

# Set API URL environment variable
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the application
CMD ["npm", "start"]
