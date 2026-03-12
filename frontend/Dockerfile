# Frontend - optional Docker deployment (Vercel is recommended for frontend)
# Build: docker build --build-arg API_URL=https://your-api.onrender.com -f frontend/Dockerfile frontend/
FROM node:20-alpine AS builder
WORKDIR /app
ARG API_URL=
COPY package.json build.js ./
COPY public/ ./public/
RUN npm install && API_URL="${API_URL}" node build.js

FROM nginx:alpine
COPY --from=builder /app/public/ /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
