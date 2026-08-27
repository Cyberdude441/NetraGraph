FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY frontend/package.json frontend/package.json
COPY frontend frontend
WORKDIR /app/frontend
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
