FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./

RUN npm config set registry https://registry.npmjs.org/
RUN npm cache clean --force
RUN npm install --legacy-peer-deps --registry=https://registry.npmjs.org/

COPY . .
RUN npm run build

FROM nginx:stable-alpine

RUN apk update && apk upgrade --no-cache && rm -rf /var/cache/apk/*

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80