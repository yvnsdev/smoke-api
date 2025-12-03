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
 && rm -rf /var/lib/apt/lists/*

# Directorio raíz del proyecto dentro del contenedor
# (coincide con lo que usas en api.py)
WORKDIR /home/tyevenes/workspace/rest_api

# 1) Copiar requirements y instalar dependencias
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 2) Copiar TODO el proyecto
#    (api.py, index.html, src/, models/, json/, fastapi/, etc.)
COPY . .

# 3) Variables de entorno que usa api.py
ENV JSON_OUTPUT_DIR=/home/tyevenes/workspace/rest_api/json \
    LOG_LEVEL=INFO \
    SAMPLE_EVERY=5

# (api.py ya se encarga de crear VIDEO_DIR, SENSOR_DIR y JSON_OUTPUT_DIR) :contentReference[oaicite:3]{index=3}

# 4) Exponer puerto
EXPOSE 8000

# 5) Arrancar FastAPI
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
