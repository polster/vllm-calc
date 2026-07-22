# syntax=docker/dockerfile:1
#
# Frontend image for vllm-calc: builds the Vite SPA and serves it with nginx.
# nginx reverse-proxies /v1/* to the backend service, so the browser talks to a
# single origin and the SPA needs no CORS config (VITE_API_BASE_URL stays empty,
# and the client falls back to same-origin relative paths — see src/api/client.ts).
#
# Build context is this web/ directory:
#   docker build -t vllm-calc-web web
# In practice it's built and run via docker/docker-compose.yml (see docker/README.md
# or `make docker-up`).

FROM node:22-slim AS builder
WORKDIR /app

# Install against the committed lockfile for reproducible builds (npm ci keeps
# devDependencies, which the build needs: `npm run build` runs tsc -b && vite build).
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Build the static SPA into /app/dist.
COPY . .
RUN npm run build


FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
