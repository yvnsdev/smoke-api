from datetime import datetime, timedelta
import re
from fastapi import FastAPI, Request, HTTPException, File, UploadFile, BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import uuid
import numpy as np
import cv2

from src.camera_inference import CameraInference
from src.utils import read_sensor_data_to_df, sensor_at

app = FastAPI()
BATCH_SIZE = 16

processing_status = {}
video_info = {}

VIDEO_DIR = Path(".tmp/videos")
SENSOR_DIR = Path(".tmp/sensors")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
SENSOR_DIR.mkdir(parents=True, exist_ok=True)

CLS_MODEL_WEIGHTS = 'models/swinv2_day_night_full.pt'
# DET_MODEL_WEIGHTS = 'models/best11_3.pt'  # ← ya no se usa

WHITELISTED_IPS = ["*"]

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if WHITELISTED_IPS != ["*"] and client_ip not in WHITELISTED_IPS:
            raise HTTPException(status_code=403, detail="IP address not allowed")
        response = await call_next(request)
        return response

app.add_middleware(IPWhitelistMiddleware)

@app.on_event("startup")
async def load_model():
    CameraInference.get_instance(
        model_name="swinv2",
        model_weights=CLS_MODEL_WEIGHTS,
        num_classes=2,
        pretrained=True,
        device="cuda:0",
        labels=["no_smoke", "smoke"],
        half=False
        # det_model_weights=DET_MODEL_WEIGHTS
    )

# VERSION SOLO CLASIFICADOR
"""
def process_video_and_sensor(video_path: Path, sensor_path: Path | None, task_id: str, include_sensors: bool = True):
    m = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", Path(video_path).stem)
    if not m:
        processing_status[task_id] = "error: cannot parse timestamp from filename"
        return

    video_start = datetime(*map(int, m.groups()))
    cls_inference = CameraInference.get_instance()

    sensor_data = None
    sensor_times = None
    if include_sensors and sensor_path is not None:
        sensor_data = read_sensor_data_to_df(sensor_path)
        if "Datetime" in sensor_data.columns and not sensor_data.empty:
            sensor_times = sensor_data["Datetime"].values.astype("datetime64[ns]")

    response: dict[str, object] = {}

    try:
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None

        frame_idx = 0
        response["filename"] = Path(video_path).name
        response["length"] = n_frames
        response["data"] = {}

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            now = video_start + timedelta(seconds=frame_idx / fps)
            s_row = None
            if include_sensors and sensor_times is not None:
                s_idx = sensor_at(now, sensor_times)
                if s_idx is not None:
                    s_row = sensor_data.iloc[s_idx]

            response["data"][frame_idx] = {"timestamp": now.isoformat()}

            # SOLO CLASIFICACIÓN
            cam_label, cam_conf = cls_inference.predict(frame)
            response["data"][frame_idx]["cls"] = {'class': cam_label, 'conf': float(cam_conf)}

            # Sensores (si aplica)
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
                response["data"][frame_idx]["sensors"] = readings

            frame_idx += 1

        cap.release()
        processed_data = response
        processing_status[task_id] = "completed"
        video_info[task_id] = processed_data

    except Exception as e:
        processing_status[task_id] = f"error: {str(e)}"
"""

# VERSION SALTO DE FRAMES
def process_video_and_sensor(video_path: Path, sensor_path: Path | None, task_id: str, include_sensors: bool = True):
    import os
    m = re.search(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", Path(video_path).stem)
    if not m:
        processing_status[task_id] = "error: cannot parse timestamp from filename"
        return

    video_start = datetime(*map(int, m.groups()))
    cls_inference = CameraInference.get_instance()

    sensor_data = None
    sensor_times = None
    if include_sensors and sensor_path is not None:
        sensor_data = read_sensor_data_to_df(sensor_path)
        if "Datetime" in sensor_data.columns and not sensor_data.empty:
            sensor_times = sensor_data["Datetime"].values.astype("datetime64[ns]")

    response: dict[str, object] = {}

    try:
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 60.0
        n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None

        SAMPLE_EVERY = int(os.getenv("SAMPLE_EVERY", "5"))

        frame_idx = 0
        response["filename"] = Path(video_path).name
        response["length"] = n_frames
        response["data"] = {}

        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            if frame_idx % SAMPLE_EVERY != 0:
                frame_idx += 1
                continue

            now = video_start + timedelta(seconds=frame_idx / fps)
            timestamp_str = now.strftime("%H:%M:%S")

            s_row = None
            if include_sensors and sensor_times is not None:
                s_idx = sensor_at(now, sensor_times)
                if s_idx is not None:
                    s_row = sensor_data.iloc[s_idx]

            response["data"][frame_idx] = {"timestamp": timestamp_str}

            cam_label, cam_conf = cls_inference.predict(frame)
            response["data"][frame_idx]["cls"] = {'class': cam_label, 'conf': float(cam_conf)}

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
                response["data"][frame_idx]["sensors"] = readings

            frame_idx += 1

        cap.release()
        processed_data = response
        processing_status[task_id] = "completed"
        video_info[task_id] = processed_data

    except Exception as e:
        processing_status[task_id] = f"error: {str(e)}"

@app.post("/upload-data/")
async def upload_video_and_sensor(
    request: Request,
    background_tasks: BackgroundTasks,
    video:   UploadFile = File(..., description="Video file"),
    sensor:  UploadFile | None = File(None, description="sensor.txt (plain-text)"),
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

        sensor_path: Path | None = None
        if sensor:
            sensor_path = SENSOR_DIR / (Path(sensor.filename).name if sensor.filename else f"{task_id}_sensor.txt")
            with sensor_path.open("wb") as s_buf:
                s_buf.write(await sensor.read())

        background_tasks.add_task(process_video_and_sensor, video_path, sensor_path, task_id, include_sensors=(sensor is not None))
        return {"task_id": task_id, "status": "files uploaded, processing started."}

    except Exception as e:
        return {"error": str(e), "status": "failure"}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    status = processing_status.get(task_id, "unknown task")
    return {"task_id": task_id, "status": status}

@app.get("/video-info/{task_id}")
async def get_video_info(task_id: str):
    if processing_status.get(task_id) == "completed":
        return video_info.get(task_id)
    else:
        return {"error": "Processing is not yet complete, please check the status."}

