FROM node:20-bullseye
WORKDIR /app

# Copy package manifests first for cached installs
COPY package.json package-lock.json* ./

# Install dependencies during image build for better caching
RUN npm install --no-audit --no-fund

# Copy application sources
COPY . .

EXPOSE 5173

CMD ["sh","-c","npm install --no-audit --no-fund && npm run dev"]
