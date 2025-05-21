FROM node:16-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY frontend/ .

# Build the application
RUN npm run build

# Install serve to run the production build
RUN npm install -g serve

# Expose port for the frontend
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "build", "-l", "3000"] 