FROM node:18

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY bundles-src ./bundles-src
RUN npx parcel build bundles-src/index.js --dist-dir bundles --public-url="/static/"
