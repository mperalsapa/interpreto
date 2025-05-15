# =========================
# STAGE 1: Build frontend
# =========================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copiar frontend
COPY interpreto-web-front/ ./interpreto-web-front/

WORKDIR /app/interpreto-web-front

# Instalar dependencias y compilar
RUN npm install && npm run build

# =========================
# STAGE 2: Final image with backend
# =========================
FROM python:3.12-slim

# Instalar dependencias necesarias del sistema
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar el backend
COPY interpreto-web-back/ ./interpreto-web-back/

# Copiar el frontend ya compilado al directorio del backend
COPY --from=frontend-builder /app/interpreto-web-front/dist/ ./interpreto-web-back/front-dist/

WORKDIR /app/interpreto-web-back

# Instalar dependencias Python
RUN pip install --no-cache-dir fastapi[standard] minio pymongo redis

# Exponer el puerto (ajustalo si usás otro)
EXPOSE 8000

# Ejecutar la app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
