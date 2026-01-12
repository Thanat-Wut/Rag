FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5173

# Run development server with host flag
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
