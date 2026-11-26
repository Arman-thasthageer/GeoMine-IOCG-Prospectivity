# Build React frontend
FROM node:22-alpine AS build

WORKDIR /app

COPY app/package*.json ./

RUN npm install

COPY app/ ./

RUN npm run build

# Serve production build using Nginx
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

COPY app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]