# 🚀 Despliegue Simple en Render (Todo en Uno)

Esta configuración ejecuta tanto el backend API como la interfaz Streamlit en un solo servicio.

## ✅ Configuración en Render

### 1. Ir a Render Dashboard
Ve a [https://dashboard.render.com/](https://dashboard.render.com/)

### 2. Crear Web Service
- Clic en **"New +"** → **"Web Service"**
- Conecta el repositorio: `yvnsdev/smoke-api`

### 3. Configuración del Servicio

**Importante:** Configura exactamente así:

| Campo | Valor |
|-------|-------|
| **Name** | `smoke-detection-app` (o cualquier nombre) |
| **Region** | Oregon (US West) o la más cercana |
| **Branch** | `main` |
| **Root Directory** | *(DEJAR COMPLETAMENTE VACÍO)* |
| **Runtime** | `Docker` |
| **Dockerfile Path** | `Dockerfile.combined` |

### 4. Variables de Entorno (Opcional)

```
LOG_LEVEL=INFO
SAMPLE_EVERY=5
```

### 5. Plan

- **Free**: Para pruebas (se duerme después de 15 min de inactividad)
- **Starter** ($7/mes): Recomendado para producción

### 6. Deploy

Clic en **"Create Web Service"**

## 🎯 ¿Qué incluye este servicio?

✅ **Backend API** (FastAPI) - Puerto 8000 interno
✅ **Frontend** (Streamlit) - Puerto expuesto al público
✅ **Modelo de IA** - Cargado automáticamente vía Git LFS

## 🌐 Acceso

Una vez desplegado, obtendrás una URL como:
```
https://smoke-detection-app.onrender.com
```

- **Interfaz Web**: `https://tu-app.onrender.com` → Streamlit
- **API Docs**: `https://tu-app.onrender.com:8000/docs` → No accesible directamente (interno)

La interfaz de Streamlit se comunica internamente con la API.

## ⚙️ Cómo funciona

El servicio usa **Supervisor** para ejecutar dos procesos:
1. **API Backend** (uvicorn) en puerto 8000
2. **Streamlit Frontend** en puerto $PORT (asignado por Render)

Ambos se comunican internamente en el mismo contenedor.

## 📊 Recursos Requeridos

- **RAM**: Mínimo 512 MB (recomendado 1 GB)
- **CPU**: 0.5 vCPU funciona bien
- **Almacenamiento**: ~1 GB (incluye modelo)

## 🔧 Troubleshooting

### "Service unavailable" o "Build failed"
- Verifica que Root Directory esté **vacío**
- Verifica que Dockerfile Path sea exactamente `Dockerfile.combined`

### "Out of Memory"
- El plan Free tiene 512 MB RAM
- Upgrade a Starter (1 GB RAM)

### El servicio se duerme
- Normal en plan Free después de 15 min
- Se reactiva automáticamente al recibir tráfico (~30 seg)
- Starter plan no se duerme

## 🔄 Actualizar

Después de hacer cambios en el código:
```bash
git add .
git commit -m "Update"
git push origin main
```

Render detectará el push y redesplegará automáticamente.

## 📱 Logs

Para ver logs en tiempo real:
1. Ve a tu servicio en Render Dashboard
2. Clic en la pestaña **"Logs"**
3. Verás logs tanto del API como de Streamlit

¡Listo! 🎉
