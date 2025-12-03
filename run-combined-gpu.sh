#!/bin/bash
set -e

# Crear red para que se vean por nombre
docker network create smoke-net || true

# Limpiar contenedor viejo si existe
docker rm -f smoke-app 2>/dev/null || true

# Construir imagen combinada
echo "🔨 Construyendo imagen..."
docker build -t smoke-app -f Dockerfile.combined .

# Ejecutar contenedor combinado con GPU
echo "🚀 Iniciando aplicación con GPU..."
docker run -d \
  --gpus all \
  --name smoke-app \
  --restart always \
  --network smoke-net \
  -p 8501:8501 \
  -p 8000:8000 \
  -e PORT=8501 \
  smoke-app

echo "✅ Aplicación iniciada con GPU!"
echo ""
echo "📊 Accede a la interfaz en: http://localhost:8501"
echo "📡 API disponible en: http://localhost:8000"
echo "📖 Documentación API: http://localhost:8000/docs"
echo ""
echo "📝 Ver logs: docker logs -f smoke-app"
echo "🔧 Detener: docker stop smoke-app"
