# ------------------------------------------
# Stage 1: Development / Builder
# ------------------------------------------
    FROM node:18-alpine AS builder

    WORKDIR /app
    
    # Copy package files first (cache-friendly)
    COPY package.json package-lock.json ./
    
    # Ensure clean deterministic install
    RUN npm ci
    
    # Copy the entire project
    COPY . .
    
    # Expose Vite dev server port
    EXPOSE 5173
    
    # Default command: run Vite in dev mode
    CMD ["npm", "run", "dev"]
    
    
    # ------------------------------------------
    # Stage 2: Production Deployment
    # ------------------------------------------
    # Uncomment this section if you want a production image
    
    # FROM node:18-alpine AS build-prod
    # WORKDIR /app
    #
    # COPY package.json package-lock.json ./
    # RUN npm ci
    #
    # COPY . .
    #
    # # Build production bundle
    # RUN npm run build
    #
    #
    # # ------------------------------------------
    # # Stage 3: Nginx Static Server
    # # ------------------------------------------
    # FROM nginx:alpine
    #
    # # Copy built frontend
    # COPY --from=build-prod /app/dist /usr/share/nginx/html
    #
    # # Optional custom config
    # # COPY nginx.conf /etc/nginx/conf.d/default.conf
    #
    # EXPOSE 80
    # CMD ["nginx", "-g", "daemon off;"]
    