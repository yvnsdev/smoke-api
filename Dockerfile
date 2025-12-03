FROM python:3.10-slim

# No .pyc y logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias del sistema para OpenCV / video
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    git \
    git-lfs \
 && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# 1) Copiar requirements y instalar dependencias
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 2) Copiar TODO el proyecto
COPY . .

# 3) Variables de entorno
ENV LOG_LEVEL=INFO \
    SAMPLE_EVERY=5

# 4) Crear directorios necesarios
RUN mkdir -p /app/fastapi/videos /app/fastapi/sensors /app/json

# 5) Exponer puerto (Render usa la variable $PORT)
EXPOSE 8000

# 6) Arrancar FastAPI con puerto dinámico
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
