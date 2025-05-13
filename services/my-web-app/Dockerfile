FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY services/my-web-app/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY services/my-web-app/ .

# Build the application
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]