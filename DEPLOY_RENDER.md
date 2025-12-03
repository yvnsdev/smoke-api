# 🚀 Guía de Despliegue en Render

## Paso 1: Preparar el repositorio (✅ Ya hecho)

El repositorio ya está configurado con:
- ✅ Git LFS para archivos grandes (modelo de 333 MB)
- ✅ Dockerfile optimizado para Render
- ✅ requirements.txt con todas las dependencias
- ✅ Rutas relativas en el código

## Paso 2: Crear Web Service en Render

1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Clic en **"New +"** → **"Web Service"**
3. Conecta tu repositorio de GitHub: `yvnsdev/smoke-api`

## Paso 3: Configuración del Servicio

### Configuración Básica:
- **Name**: `smoke-api` (o el nombre que prefieras)
- **Region**: `Oregon (US West)` (o la más cercana)
- **Branch**: `main`
- **Root Directory**: (dejar vacío)

### Build & Deploy:
- **Runtime**: `Docker`
- **Dockerfile Path**: `./Dockerfile`

### Plan:
- **Instance Type**: 
  - **Free** (para pruebas, con limitaciones)
  - **Starter** ($7/mes, recomendado para producción)
  - **Standard** (si necesitas más recursos)

### Variables de Entorno (Opcional):
```
LOG_LEVEL=INFO
SAMPLE_EVERY=5
```

## Paso 4: Deploy

1. Clic en **"Create Web Service"**
2. Render automáticamente:
   - Clonará tu repositorio
   - Descargará archivos de Git LFS (el modelo)
   - Construirá la imagen Docker
   - Desplegará el servicio

⏱️ **Tiempo estimado**: 5-10 minutos (primera vez)

## Paso 5: Verificar el Despliegue

Una vez desplegado, obtendrás una URL como:
```
https://smoke-api-xxxx.onrender.com
```

Prueba los endpoints:
- `GET https://smoke-api-xxxx.onrender.com/` - Health check
- `GET https://smoke-api-xxxx.onrender.com/docs` - Documentación Swagger

## 🎯 Desplegar la Interfaz Streamlit (Opcional)

Para desplegar también la interfaz de Streamlit:

1. Crear otro Web Service en Render
2. Mismo repositorio: `yvnsdev/smoke-api`
3. Configuración:
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile.streamlit`
   - **Environment Variable**:
     ```
     API_BASE=https://smoke-api-xxxx.onrender.com
     ```
     (Usa la URL del servicio API que desplegaste antes)

## ⚠️ Consideraciones Importantes

### Git LFS
- ✅ Render soporta Git LFS automáticamente
- El modelo (333 MB) se descargará correctamente

### Recursos
- El modelo requiere ~500MB de RAM mínimo
- CPU: Funciona bien (sin GPU en Render free/starter)
- GPU: No disponible en planes básicos de Render

### Límites del Plan Free
- Se duerme después de 15 minutos de inactividad
- 750 horas/mes de uso
- Arranque lento (~30 segundos después de dormir)

### Almacenamiento Temporal
- Los videos subidos se almacenan temporalmente
- Se eliminan en cada redeploy o restart
- Para persistencia, considera usar almacenamiento externo (S3, etc.)

## 🔧 Troubleshooting

### Error: "Out of Memory"
- Upgrade a plan con más RAM
- El modelo carga ~500MB en memoria

### Build lento
- Normal la primera vez (descarga modelo con LFS)
- Builds subsecuentes son más rápidos (cache)

### Error de Git LFS
- Verifica que `.gitattributes` esté en el repo
- Confirma que el modelo esté en LFS: `git lfs ls-files`

## 📱 Monitoreo

En el dashboard de Render puedes ver:
- Logs en tiempo real
- Métricas de CPU/RAM
- Estado de despliegues
- Configuración de dominios personalizados

## 🔄 Actualizar el Servicio

Para actualizar después de cambios:
```bash
git add .
git commit -m "Update"
git push origin main
```

Render automáticamente detectará el push y redesplegará.

## 🌐 URL Final

Tu API estará disponible en:
```
https://[tu-nombre-de-servicio].onrender.com
```

¡Listo! 🎉
