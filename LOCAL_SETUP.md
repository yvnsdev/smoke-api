# 🚀 Ejecutar Aplicación Localmente (Todo en Uno)

Esta configuración ejecuta tanto el backend API como la interfaz Streamlit en un solo contenedor Docker.

## 📋 Pre-requisitos

- Docker instalado
- (Opcional) nvidia-docker para usar GPU

## 🏃 Ejecución Rápida

### Opción 1: CPU (Sin GPU)
```bash
./run-combined.sh
```

### Opción 2: GPU (Con nvidia-docker)
```bash
./run-combined-gpu.sh
```

## 🌐 Acceder a la Aplicación

Una vez iniciado, accede a:

- **🖥️ Interfaz Web (Streamlit)**: http://localhost:8501
- **📡 API Backend**: http://localhost:8000
- **📖 Documentación API**: http://localhost:8000/docs

## 📝 Comandos Útiles

### Ver logs en tiempo real
```bash
docker logs -f smoke-app
```

### Detener la aplicación
```bash
docker stop smoke-app
```

### Reiniciar la aplicación
```bash
docker restart smoke-app
```

### Eliminar el contenedor
```bash
docker rm -f smoke-app
```

### Reconstruir desde cero
```bash
# Detener y eliminar
docker rm -f smoke-app

# Reconstruir imagen
docker build -t smoke-app -f Dockerfile.combined .

# Ejecutar de nuevo
./run-combined.sh  # o ./run-combined-gpu.sh
```

## 🔧 Arquitectura

El contenedor ejecuta:

1. **Backend API** (FastAPI) → Puerto 8000
   - Procesa videos
   - Ejecuta modelo de IA
   - Gestiona tareas en segundo plano

2. **Frontend** (Streamlit) → Puerto 8501
   - Interfaz web para cargar videos
   - Visualización de resultados
   - Descarga de JSON

3. **Supervisor** → Gestiona ambos procesos
   - Mantiene ambos servicios corriendo
   - Auto-reinicio en caso de fallos
   - Logs separados

## 📊 Recursos

- **RAM**: ~1-2 GB
- **CPU**: 2 cores recomendado
- **GPU**: Opcional (mejora velocidad de inferencia)
- **Disco**: ~2 GB (incluye modelo)

## 🐛 Troubleshooting

### El contenedor no inicia
```bash
# Ver logs para diagnosticar
docker logs smoke-app
```

### Error de GPU
Si ves error de GPU y no tienes nvidia-docker:
```bash
# Usa la versión sin GPU
./run-combined.sh
```

### Puerto ya en uso
Si los puertos 8000 o 8501 están ocupados:
```bash
# Modificar run-combined.sh y cambiar los puertos:
# -p 8502:8501 \  # Cambia 8501 por otro puerto
# -p 8001:8000 \  # Cambia 8000 por otro puerto
```

### Limpiar todo y empezar de cero
```bash
# Detener contenedor
docker rm -f smoke-app

# Eliminar imagen
docker rmi smoke-app

# Ejecutar script nuevamente
./run-combined.sh
```

## 📁 Archivos Importantes

- `Dockerfile.combined` - Configuración del contenedor
- `supervisord.conf` - Configuración de supervisor
- `run-combined.sh` - Script de ejecución (CPU)
- `run-combined-gpu.sh` - Script de ejecución (GPU)

## 🔄 Actualizar después de cambios

Si modificas el código:

```bash
# Detener contenedor actual
docker rm -f smoke-app

# Ejecutar script (reconstruye automáticamente)
./run-combined.sh
```

¡Listo! 🎉
