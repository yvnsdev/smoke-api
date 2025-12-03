#!/bin/bash
set -e

# Crear red para que se vean por nombre
docker network create smoke-net || true

# Limpiar contenedor viejo si existe
docker rm -f smoke-app 2>/dev/null || true

# Construir imagen combinada
echo "🔨 Construyendo imagen..."
docker build -t smoke-app -f Dockerfile.combined .

# Ejecutar contenedor combinado
# Si tienes GPU y nvidia-docker instalado, descomenta la línea con --gpus all
echo "🚀 Iniciando aplicación..."
docker run -d \
  --name smoke-app \
  --restart always \
  --network smoke-net \
  -p 8501:8501 \
  -p 8000:8000 \
  -e PORT=8501 \
  smoke-app

echo "✅ Aplicación iniciada!"
echo ""
echo "📊 Accede a la interfaz en: http://localhost:8501"
echo "📡 API disponible en: http://localhost:8000"
echo "📖 Documentación API: http://localhost:8000/docs"
echo ""
echo "📝 Ver logs: docker logs -f smoke-app"
