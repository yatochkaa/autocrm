# Сборка SPA → раздача через nginx с прокси /api → бэкенд.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
# Адрес API; переопределяется в docker-compose / Railway.
ENV API_UPSTREAM=http://api:8000
COPY --from=build /app/dist /usr/share/nginx/html
# Шаблон подставляет ${API_UPSTREAM} на старте контейнера (стандартный механизм nginx-образа).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
