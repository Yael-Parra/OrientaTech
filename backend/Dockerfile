# ===================================
# OrientaTech Backend - Dockerfile SIMPLE
# ===================================

FROM python:3.11-slim AS builder

# Variables de entorno básicas
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar solo lo mínimo necesario
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependencias mínimas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

EXPOSE 8000

# Ejecutar como root por simplicidad
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
