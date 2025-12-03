from datetime import datetime, timedelta
import re
import json
import os
import logging
from typing import Optional, Dict, Any
from copy import deepcopy

from fastapi import FastAPI, Request, HTTPException, File, UploadFile, BackgroundTasks, Query
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import uuid
import numpy as np
import cv2
import torch

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_EVERY_N = int(os.getenv("LOG_EVERY_N", "50"))
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("smoke-api")

# --- modelos / utilidades ---
# from src.camera import CameraInference      # ← original
from src.camera_inference import CameraInference  # ← SOLO CLASIFICACIÓN
from src.utils import read_sensor_data_to_df, sensor_at

app = FastAPI()

processing_status: Dict[str, str] = {}
video_info: Dict[str, dict] = {}

ROOT = Path(__file__).resolve().parent

# Usar rutas relativas para compatibilidad con Render y otros servicios
BASE_DIR = ROOT / "fastapi"
VIDEO_DIR = BASE_DIR / "videos"
SENSOR_DIR = BASE_DIR / "sensors"
JSON_OUTPUT_DIR = ROOT / "json"

# Permitir override por variable de entorno
if json_dir_env := os.getenv("JSON_OUTPUT_DIR"):
    JSON_OUTPUT_DIR = Path(json_dir_env).resolve()

for p in (VIDEO_DIR, SENSOR_DIR, JSON_OUTPUT_DIR):
    p.mkdir(parents=True, exist_ok=True)

CLS_MODEL_WEIGHTS = str(ROOT / "models/swinv2_day_night_full.pt")
# DET_MODEL_WEIGHTS = str(ROOT / "models/best11_3.pt")  # ← ya no se usa

WHITELISTED_IPS = ["*"]

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if WHITELISTED_IPS != ["*"] and client_ip not in WHITELISTED_IPS:
            log.warning("[IP BLOCKED] %s", client_ip)
            raise HTTPException(status_code=403, detail="IP address not allowed")
        return await call_next(request)

app.add_middleware(IPWhitelistMiddleware)
"""
@app.on_event("startup")
async def load_model():
    device = "cuda:0"
    log.info("Inicializando modelo de CLASIFICACIÓN | device=%s", device)
    CameraInference.get_instance(
        model_name="swinv2",
        model_weights=CLS_MODEL_WEIGHTS,
        num_classes=2,
        pretrained=True,
        device=device,
        labels=["no_smoke", "smoke"],
        half=False,
        # det_model_weights=DET_MODEL_WEIGHTS  # ← eliminado
    )
    log.info("Modelo de clasificación listo")

def _strip_sensors(payload: dict) -> dict:
    out = deepcopy(payload)
    for _, frame in list(out.get("data", {}).items()):
        if isinstance(frame, dict) and "sensors" in frame:
            del frame["sensors"]
    return out
"""

@app.on_event("startup")
async def load_model():
    import torch
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    log.info("Inicializando modelo de CLASIFICACIÓN | device=%s", device)
    CameraInference.get_instance(
        model_name="swinv2",
        model_weights=CLS_MODEL_WEIGHTS,
        num_classes=2,
        pretrained=True,
        device=device,
        labels=["no_smoke", "smoke"],
        half=False,
    )
    log.info("Modelo de clasificación listo")

# VERSION SOLO CLASIFICADOR
"""
def process_video_and_sensor(
    video_path: Path,
    sensor_path: Optional[Path],
    task_id: str,
    include_sensors: bool = True
):
    try:
        m = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", video_path.stem)
        if not m:
            processing_status[task_id] = "error: cannot parse timestamp from filename"
            log.error("[TASK %s] No pude parsear timestamp de %s", task_id, video_path.name)
            return
        video_start = datetime(*map(int, m.groups()))
        nice_ts = video_start.strftime("%Y%m%d_%H%M%S")

        infer = CameraInference.get_instance()

        sensor_data = None
        sensor_times = None
        if include_sensors and sensor_path is not None and sensor_path.exists():
            try:
                sensor_data = read_sensor_data_to_df(sensor_path)
                if "Datetime" in sensor_data.columns and not sensor_data.empty:
                    sensor_times = sensor_data["Datetime"].values.astype("datetime64[ns]")
                log.info("[TASK %s] sensores cargados: %d filas", task_id, 0 if sensor_data is None else len(sensor_data))
            except Exception as e:
                log.warning("[TASK %s] error leyendo sensores: %s", task_id, e)
                sensor_data = None
                sensor_times = None

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            processing_status[task_id] = "error: cannot open video"
            log.error("[TASK %s] No pude abrir video %s", task_id, video_path)
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None
        log.info("[TASK %s] procesando video | fps=%.2f | frames=%s", task_id, fps, n_frames)

        frame_idx = 0
        response: Dict[str, Any] = {"filename": video_path.name, "length": n_frames, "data": {}}

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            now = video_start + timedelta(seconds=frame_idx / fps)

            # --- SOLO CLASIFICACIÓN ---
            cam_label, cam_conf = infer.predict(frame)

            entry = {
                "timestamp": now.isoformat(),
                "cls": {"class": cam_label, "conf": float(cam_conf)}
            }

            # --- sensores (opcional) ---
            s_row = None
            if include_sensors and (sensor_times is not None):
                s_idx = sensor_at(now, sensor_times)
                if s_idx is not None:
                    s_row = sensor_data.iloc[s_idx]

            if include_sensors:
                if s_row is not None:
                    readings = {
                        "Temp": float(s_row.get("Temp", np.nan)),
                        "Humidity": float(s_row.get("Humidity", np.nan)),
                        "CO2": float(s_row.get("CO2", np.nan)),
                        "PM1": float(s_row.get("PM1", np.nan)),
                        "PM2.5": float(s_row.get("PM2.5", np.nan)),
                        "PM10": float(s_row.get("PM10", np.nan)),
                    }
                else:
                    readings = {"Temp": -1.0, "Humidity": -1.0, "CO2": -1.0, "PM1": -1.0, "PM2.5": -1.0, "PM10": -1.0}
                entry["sensors"] = readings

            response["data"][frame_idx] = entry

            if LOG_EVERY_N and (frame_idx % LOG_EVERY_N == 0):
                log.info("[frame %d] %s | cls=%s(%.3f)",
                         frame_idx, now.isoformat(), cam_label, float(cam_conf))
            frame_idx += 1

        cap.release()
        video_info[task_id] = response

        out_by_id = (JSON_OUTPUT_DIR / f"{task_id}.json")
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", video_path.stem)
        out_friendly = (JSON_OUTPUT_DIR / f"{nice_ts}_{safe_stem}.json")
        try:
            with out_by_id.open("w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            with out_friendly.open("w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
            log.info("[TASK %s] JSONs guardados -> %s | %s", task_id, out_by_id, out_friendly)
        except Exception as e:
            log.warning("[TASK %s] no pude guardar JSON: %s", task_id, e)

        processing_status[task_id] = "completed"
        log.info("[TASK %s] COMPLETADO", task_id)

    except Exception as e:
        processing_status[task_id] = f"error: {str(e)}"
        log.exception("[TASK %s] ERROR no controlado: %s", task_id, e)
"""

# VERSION CON SALTO DE FRAMES
def process_video_and_sensor(
    video_path: Path,
    sensor_path: Optional[Path],
    task_id: str,
    include_sensors: bool = True
):
    import os
    try:
        m = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", video_path.stem)
        if not m:
            processing_status[task_id] = "error: cannot parse timestamp from filename"
            log.error("[TASK %s] No pude parsear timestamp de %s", task_id, video_path.name)
            return
        video_start = datetime(*map(int, m.groups()))
        nice_ts = video_start.strftime("%Y%m%d_%H%M%S")

        infer = CameraInference.get_instance()

        sensor_data = None
        sensor_times = None
        if include_sensors and sensor_path is not None and sensor_path.exists():
            try:
                sensor_data = read_sensor_data_to_df(sensor_path)
                if "Datetime" in sensor_data.columns and not sensor_data.empty:
                    sensor_times = sensor_data["Datetime"].values.astype("datetime64[ns]")
                log.info("[TASK %s] sensores cargados: %d filas", task_id, 0 if sensor_data is None else len(sensor_data))
            except Exception as e:
                log.warning("[TASK %s] error leyendo sensores: %s", task_id, e)
                sensor_data = None
                sensor_times = None

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            processing_status[task_id] = "error: cannot open video"
            log.error("[TASK %s] No pude abrir video %s", task_id, video_path)
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None
        log.info("[TASK %s] procesando video | fps=%.2f | frames=%s", task_id, fps, n_frames)

        SAMPLE_EVERY = int(os.getenv("SAMPLE_EVERY", "10"))

        frame_idx = 0
        response: Dict[str, Any] = {"filename": video_path.name, "length": n_frames, "data": {}}

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_idx % SAMPLE_EVERY != 0:
                frame_idx += 1
                continue

            # timestamp formateado como HH:MM:SS
            now = video_start + timedelta(seconds=frame_idx / fps)
            timestamp_str = now.strftime("%H:%M:%S")

            cam_label, cam_conf = infer.predict(frame)

            entry = {
                "timestamp": timestamp_str,
                "cls": {"class": cam_label, "conf": float(cam_conf)}
            }

            s_row = None
            if include_sensors and (sensor_times is not None):
                s_idx = sensor_at(now, sensor_times)
                if s_idx is not None:
                    s_row = sensor_data.iloc[s_idx]

            if include_sensors:
                if s_row is not None:
                    readings = {
                        "Temp": float(s_row.get("Temp", np.nan)),
                        "Humidity": float(s_row.get("Humidity", np.nan)),
                        "CO2": float(s_row.get("CO2", np.nan)),
                        "PM1": float(s_row.get("PM1", np.nan)),
                        "PM2.5": float(s_row.get("PM2.5", np.nan)),
                        "PM10": float(s_row.get("PM10", np.nan)),
                    }
                else:
                    readings = {"Temp": -1.0, "Humidity": -1.0, "CO2": -1.0,
                                "PM1": -1.0, "PM2.5": -1.0, "PM10": -1.0}
                entry["sensors"] = readings

            response["data"][frame_idx] = entry

            if LOG_EVERY_N and (frame_idx % LOG_EVERY_N == 0):
                log.info("[frame %d] %s | cls=%s(%.3f)",
                         frame_idx, timestamp_str, cam_label, float(cam_conf))
            frame_idx += 1

        cap.release()
        video_info[task_id] = response

        out_by_id = (JSON_OUTPUT_DIR / f"{task_id}.json")
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", video_path.stem)
        out_friendly = (JSON_OUTPUT_DIR / f"{nice_ts}_{safe_stem}.json")
        with out_by_id.open("w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        with out_friendly.open("w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        log.info("[TASK %s] JSONs guardados -> %s | %s",
                 task_id, out_by_id, out_friendly)

        processing_status[task_id] = "completed"
        log.info("[TASK %s] COMPLETADO", task_id)

    except Exception as e:
        processing_status[task_id] = f"error: {str(e)}"
        log.exception("[TASK %s] ERROR no controlado: %s", task_id, e)

@app.post("/upload-data/")
async def upload_video_and_sensor(
    request: Request,
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file"),
    sensor: UploadFile | None = File(None, description="sensor.txt (plain-text)"),
):
    try:
        if video.content_type not in {"video/mp4", "video/avi", "video/mov", "application/octet-stream"}:
            raise HTTPException(status_code=400, detail="Unsupported video MIME type.")
        if sensor and sensor.content_type not in {"text/plain"}:
            raise HTTPException(status_code=400, detail="sensor file must be text/plain")

        task_id = str(uuid.uuid4())
        processing_status[task_id] = "processing"

        video_path = VIDEO_DIR / Path(video.filename).name
        with video_path.open("wb") as buffer:
            while True:
                if await request.is_disconnected():
                    buffer.close()
                    video_path.unlink(missing_ok=True)
                    processing_status[task_id] = "aborted"
                    return {"error": "Client disconnected during upload", "status": "failure"}
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)

        sensor_path: Optional[Path] = None
        if sensor:
            sensor_path = SENSOR_DIR / (Path(sensor.filename).name if sensor.filename else f"{task_id}_sensor.txt")
            with sensor_path.open("wb") as s_buf:
                s_buf.write(await sensor.read())

        background_tasks.add_task(
            process_video_and_sensor,
            video_path,
            sensor_path,
            task_id,
            include_sensors=(sensor is not None)
        )

        return {"task_id": task_id, "status": "files uploaded, processing started."}

    except Exception as e:
        log.exception("Upload ERROR: %s", e)
        return {"error": str(e), "status": "failure"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    return {"task_id": task_id, "status": processing_status.get(task_id, "unknown task")}

@app.get("/video-info/{task_id}")
async def get_video_info(task_id: str, video_only: bool = Query(False, description="Si True, omite sensores")):
    if processing_status.get(task_id) == "completed":
        payload = video_info.get(task_id)
        if not isinstance(payload, dict):
            return {"error": "No data for task_id."}
        return _strip_sensors(payload) if video_only else payload
    else:
        return {"error": "Processing is not yet complete, please check the status."}

@app.get("/video-json/{task_id}")
async def get_video_json_file(task_id: str, video_only: bool = Query(False, description="True = omite sensores")):
    json_path = (JSON_OUTPUT_DIR / f"{task_id}.json").resolve()
    if not json_path.exists():
        return {"error": f"No existe {json_path}. ¿Terminó el procesamiento?"}

    if not video_only:
        return FileResponse(json_path, media_type="application/json", filename=f"{task_id}.json")

    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    data_no_sensors = _strip_sensors(payload)
    tmp_path = (JSON_OUTPUT_DIR / f"{task_id}_video_only.json").resolve()
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data_no_sensors, f, ensure_ascii=False, indent=2)
    return FileResponse(tmp_path, media_type="application/json", filename=f"{task_id}_video_only.json")

