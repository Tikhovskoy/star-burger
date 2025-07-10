FROM node:17.6.0-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY bundles-src ./bundles-src
RUN npx parcel build bundles-src/index.js --dist-dir bundles --public-url="/static/"
