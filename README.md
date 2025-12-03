# Smoke Detection API

Sistema de detección de humo en videos usando inteligencia artificial.

## 🚀 Características

- 🎥 Procesamiento de videos para detección de humo
- 🤖 Modelo de IA basado en Swin Transformer V2
- 📊 API REST con FastAPI
- 🖥️ Interfaz web con Streamlit
- 📦 Manejo de archivos grandes con Git LFS

## 🛠️ Tecnologías

- **Backend**: FastAPI + PyTorch
- **Frontend**: Streamlit
- **IA**: Swin Transformer V2
- **Contenedores**: Docker
- **Almacenamiento**: Git LFS

## 📋 Requisitos

- Python 3.10+
- CUDA (opcional, para GPU)
- Docker (para despliegue)

## 🔧 Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/yvnsdev/smoke-api.git
cd smoke-api

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API
uvicorn api:app --host 0.0.0.0 --port 8000

# Ejecutar interfaz (en otra terminal)
streamlit run app_streamlit.py
```

## 🐳 Docker

```bash
# Construir imágenes
docker build -t smoke-api -f Dockerfile .
docker build -t smoke-ui -f Dockerfile.streamlit .

# Ejecutar con el script
./run.sh
```

## 📡 API Endpoints

- `POST /upload-data/` - Subir video para análisis
- `GET /status/{task_id}` - Consultar estado de procesamiento
- `GET /video-info/{task_id}` - Obtener resultados del análisis

## 🌐 Despliegue

### Render

1. Conecta tu repositorio de GitHub
2. Selecciona "Web Service"
3. Configuración automática con Dockerfile
4. Variables de entorno opcionales:
   - `LOG_LEVEL`: INFO (por defecto)
   - `SAMPLE_EVERY`: 5 (frames)

## 📄 Licencia

MIT
