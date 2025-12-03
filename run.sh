#!/bin/bash
set -e

# Crear red para que se vean por nombre
docker network create smoke-net || true

# Limpiar contenedores viejos si existen
docker rm -f smoke-api smoke-ui 2>/dev/null || true

# Backend (SOLO dentro de la red, sin exponer puerto)
# Si tienes GPU y nvidia-docker instalado, agrega: --gpus all
docker run -d \
  --name smoke-api \
  --restart always \
  --network smoke-net \
  smoke-api

# Front Streamlit (expuesto al mundo por puerto 80)
docker run -d \
  --name smoke-ui \
  --restart always \
  --network smoke-net \
  -p 80:8501 \
  -e API_BASE=http://smoke-api:8000 \
  smoke-ui

