import os
import time
import json
import requests
import streamlit as st  # :contentReference[oaicite:0]{index=0}

# URL del backend FastAPI (dentro del servidor suele ser http://localhost:8000)
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="Smoke Detection API",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Sistema de Detección de Humo con IA")
st.markdown("""
**Plataforma de procesamiento de videos** para detección automática de humo usando inteligencia artificial.
- 📤 **Carga videos** de hasta **50 GB**
- 🔍 **Consulta** el estado de procesamiento en tiempo real
- 📥 **Descarga** resultados en formato JSON
- 📊 **Visualiza** análisis frame por frame
""")

st.markdown("---")


def build_execution_log(info_json: dict, max_lines: int = 200) -> str:
    """Construye un texto tipo 'log' a partir del JSON de salida."""
    data = info_json.get("data", {})
    if not isinstance(data, dict) or not data:
        return "// No hay datos de frames en el resultado."

    # Claves de frames pueden venir como strings desde JSON
    try:
        sorted_keys = sorted(data.keys(), key=lambda k: int(k))
    except Exception:
        sorted_keys = list(data.keys())

    lines = []
    for k in sorted_keys:
        entry = data.get(k, {})
        frame_idx = k
        try:
            frame_idx = int(k)
        except Exception:
            pass

        ts = entry.get("timestamp", "??:??:??")
        cls = entry.get("cls", {}) or {}
        label = cls.get("class", "unknown")
        conf = cls.get("conf", None)

        if conf is not None:
            line = f"[frame {frame_idx}] {ts} | cls={label} (conf={conf:.3f})"
        else:
            line = f"[frame {frame_idx}] {ts} | cls={label}"

        lines.append(line)
        if len(lines) >= max_lines:
            lines.append(f"... ({len(data)} frames totales, mostrando solo {max_lines})")
            break

    return "\n".join(lines)


def render_task_inspection(task_id: str, auto_download: bool = False):
    """Consulta estado + JSON + 'logs' para un task_id dado."""
    if not task_id:
        st.warning("Ingresa un ID de tarea para consultar.")
        return

    # 1) Estado
    try:
        status_resp = requests.get(f"{API_BASE}/status/{task_id}")
    except Exception as e:
        st.error(f"❌ Error al conectar con el backend: {e}")
        return

    if not status_resp.ok:
        st.error(
            f"❌ Error HTTP {status_resp.status_code} al consultar estado: {status_resp.text}"
        )
        return

    status_data = status_resp.json()
    status = status_data.get("status", "desconocido")
    
    # Mostrar estado con colores
    if status == "completed":
        st.success(f"✅ **Estado de la tarea `{task_id}`**: Completada")
    elif status == "processing":
        st.info(f"⏳ **Estado de la tarea `{task_id}`**: Procesando...")
    elif status.startswith("error"):
        st.error(f"❌ **Estado de la tarea `{task_id}`**: {status}")
    else:
        st.warning(f"⚠️ **Estado de la tarea `{task_id}`**: {status}")

    if status != "completed":
        st.info("💡 La tarea aún no está completada. Vuelve a intentar en unos segundos.")
        return

    # 2) Obtener JSON del backend
    try:
        info_resp = requests.get(f"{API_BASE}/video-info/{task_id}")
    except Exception as e:
        st.error(f"❌ Error al obtener video-info: {e}")
        return

    if not info_resp.ok:
        st.error(
            f"❌ Error HTTP {info_resp.status_code} al obtener video-info: {info_resp.text}"
        )
        return

    info_json = info_resp.json()
    if isinstance(info_json, dict) and info_json.get("error"):
        st.error(f"❌ El backend devolvió un error: {info_json['error']}")
        return

    # Preparar JSON para descarga
    json_str = json.dumps(info_json, ensure_ascii=False, indent=2)
    
    # 3) Botón de descarga prominente
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Descargar Resultados (JSON)",
            data=json_str,
            file_name=f"deteccion_humo_{task_id}.json",
            mime="application/json",
            key=f"download_json_{task_id}",
            use_container_width=True,
            type="primary"
        )
    
    st.markdown("---")
    
    # 4) Mostrar estadísticas resumidas
    data = info_json.get("data", {})
    if data:
        total_frames = len(data)
        st.metric("Total de Frames Analizados", f"{total_frames:,}")
    
    # 5) Opción para ver detalles
    with st.expander("📊 Ver análisis detallado", expanded=auto_download):
        # Tabs para organizar información
        tab1, tab2 = st.tabs(["📜 Log de Ejecución", "📄 JSON Completo"])
        
        with tab1:
            logs_text = build_execution_log(info_json, max_lines=500)
            st.text_area("Log de frames procesados", logs_text, height=400)
        
        with tab2:
            st.json(info_json)


# --- UI con pestañas ---
tab_upload, tab_query = st.tabs(["📥 Subir nuevo video", "🔎 Consultar tarea existente"])

# ---------------------------------------------------------------------
# TAB 1: SUBIR Y PROCESAR VIDEO
# ---------------------------------------------------------------------
with tab_upload:
    st.markdown("### 📥 Cargar Video para Análisis")

    st.info(
        "📹 **Formatos soportados**: MP4, AVI, MOV, MKV\n\n"
        "💾 **Tamaño máximo**: 50 GB\n\n"
        "📄 **Archivo de sensores** (opcional): Datos complementarios en formato TXT"
    )

    col1, col2 = st.columns(2)
    
    with col1:
        video_file = st.file_uploader(
            "🎥 Selecciona el video",
            type=["mp4", "avi", "mov", "mkv"],
            key="video_uploader",
            help="Archivo de video para análisis (máx. 50 GB)"
        )
    
    with col2:
        sensor_file = st.file_uploader(
            "📄 Archivo de sensores (opcional)",
            type=["txt"],
            key="sensor_uploader",
            help="Datos adicionales de sensores en formato TXT"
        )

    status_placeholder = st.empty()
    progress_placeholder = st.empty()

    if st.button("🚀 Subir y procesar", key="btn_upload"):
        if not video_file:
            st.error("Debes seleccionar un video antes de continuar.")
        else:
            try:
                files = {
                    "video": (
                        video_file.name,
                        video_file,
                        video_file.type or "video/mp4",
                    ),
                }
                if sensor_file:
                    files["sensor"] = (
                        sensor_file.name,
                        sensor_file,
                        "text/plain",
                    )

                status_placeholder.info("Subiendo archivo(s) al backend…")

                # 1) POST /upload-data/
                resp = requests.post(f"{API_BASE}/upload-data/", files=files)
                if not resp.ok:
                    st.error(
                        f"Error HTTP {resp.status_code} al subir datos:\n{resp.text}"
                    )
                    st.stop()

                data = resp.json()
                task_id = data.get("task_id")
                if not task_id:
                    st.error(f"La respuesta del backend no contiene task_id: {data}")
                    st.stop()

                status_placeholder.success(
                    f"Tarea creada: **{task_id}**\n\n"
                    f"Estado inicial: `{data.get('status', 'desconocido')}`"
                )

                # 2) Polling /status/{task_id}
                progress_bar = progress_placeholder.progress(0, text="Procesando video…")
                poll_steps = 0
                max_steps = 100  # solo para la barra visual

                while True:
                    time.sleep(2.0)
                    poll_steps = min(poll_steps + 1, max_steps)
                    progress_bar.progress(
                        poll_steps / max_steps, text="Procesando video…"
                    )

                    status_resp = requests.get(f"{API_BASE}/status/{task_id}")
                    if not status_resp.ok:
                        st.error(
                            f"Error HTTP {status_resp.status_code} al consultar estado."
                        )
                        st.stop()

                    status_data = status_resp.json()
                    status = status_data.get("status", "desconocido")
                    status_placeholder.info(
                        f"Estado de la tarea **{task_id}**: `{status}`"
                    )

                    if status.startswith("error"):
                        progress_bar.empty()
                        st.error(
                            f"Ocurrió un error durante el procesamiento: {status}"
                        )
                        break

                    if status == "completed":
                        progress_bar.empty()
                        status_placeholder.success(
                            f"✅ Tarea {task_id} completada."
                        )
                        break

                # 3) Al terminar, reutilizamos el mismo flujo que en la pestaña de consulta
                if status == "completed":
                    st.markdown("---")
                    st.success(
                        f"🎉 **Procesamiento completado exitosamente**\n\n"
                        f"ID de tarea: `{task_id}`"
                    )
                    render_task_inspection(task_id, auto_download=True)

            except Exception as e:
                st.error(f"Error al comunicarse con el backend: {e}")

# ---------------------------------------------------------------------
# TAB 2: CONSULTAR TAREA EXISTENTE
# ---------------------------------------------------------------------
with tab_query:
    st.markdown("### 🔎 Consultar Tarea Existente")

    st.info(
        "💡 **¿Cómo obtener un ID de tarea?**\n\n"
        "Cada vez que cargas un video, el sistema genera un ID único. "
        "Usa ese ID aquí para consultar el estado y descargar resultados."
    )

    col1, col2 = st.columns([3, 1])
    
    with col1:
        task_id_input = st.text_input(
            "ID de tarea", 
            key="task_id_query",
            placeholder="Ej: task_1234567890"
        )
    
    with col2:
        st.write("")
        st.write("")
        query_button = st.button(
            "🔍 Consultar", 
            key="btn_query",
            use_container_width=True,
            type="primary"
        )

    if query_button:
        if task_id_input.strip():
            render_task_inspection(task_id_input.strip())
        else:
            st.warning("⚠️ Por favor ingresa un ID de tarea válido.")

