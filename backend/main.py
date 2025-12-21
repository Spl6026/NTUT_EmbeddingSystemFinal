import os
import shutil
import requests
import logging
from models import ParkingViolationLog
from starlette.requests import ClientDisconnect
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends, Request, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from PIL import Image
import numpy as np
from ssh_tunnel import start_ssh_tunnel

ssh_proc = start_ssh_tunnel()

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

AI_HOST = os.getenv("AI_SERVICE_URL", "http://localhost:5000")
VEHICLE_API_URL = f"{AI_HOST}/predict/vehicle"
REDLINE_API_URL = f"{AI_HOST}/predict/redline"

LIVE_IMG_FILENAME = "live.jpg"
LIVE_IMG_PATH = f"static/{LIVE_IMG_FILENAME}"

latest_cache = {
    "id": 0,
    "timestamp": None,
    "is_violation": False,
    "car_detected": False,
    "status": "System Ready",
    "image_url": None
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def yolo_to_bbox(yolo_box, img_w, img_h):
    # yolo_box = [xc, yc, w, h] (0~1)
    if not yolo_box or len(yolo_box) != 4:
        return None

    xc, yc, w, h = yolo_box

    x1 = int((xc - w / 2) * img_w)
    y1 = int((yc - h / 2) * img_h)
    x2 = int((xc + w / 2) * img_w)
    y2 = int((yc + h / 2) * img_h)

    return [x1, y1, x2, y2]


def check_intersection(boxA, boxB):
    # box = [x1, y1, x2, y2]

    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interWidth = max(0, xB - xA)
    interHeight = max(0, yB - yA)

    return interWidth > 0 and interHeight > 0


def decode_rgb565(raw_bytes, w, h):
    # 將 bytes 轉為 uint16 數組 (Big-endian)
    data = np.frombuffer(raw_bytes, dtype='>u2')

    # 提取顏色分量
    r = ((data & 0x1F) << 3).astype(np.uint8)  # Low 5 bits
    g = (((data >> 5) & 0x3F) << 2).astype(np.uint8)  # Mid 6 bits
    b = (((data >> 11) & 0x1F) << 3).astype(np.uint8)  # High 5 bits

    # 合併成 RGB 並轉為圖片
    rgb = np.stack((r, g, b), axis=-1).reshape((h, w, 3))
    return Image.fromarray(rgb)


def detect_parking(img_w, img_h):
    global latest_cache
    logger.info(f"Image size: {img_w}x{img_h}")
    car_count = 0
    car_boxes = []
    red_line_detected = False
    red_line_box = []
    is_violation = False
    status_msg = "Analyzing..."

    try:
        # 呼叫車輛模型
        with open(LIVE_IMG_PATH, 'rb') as f_veh:
            resp_veh = requests.post(VEHICLE_API_URL, files={'file': f_veh}, timeout=5)
            if resp_veh.status_code == 200:
                v_data = resp_veh.json()
                car_count = v_data.get("car_count", 0)
                car_boxes = v_data.get("boxes", [])  # list of { "box": [x,y,w,h] }

        # 呼叫紅線模型
        with open(LIVE_IMG_PATH, 'rb') as f_red:
            resp_red = requests.post(REDLINE_API_URL, files={'file': f_red}, timeout=5)
            if resp_red.status_code == 200:
                r_data = resp_red.json()
                red_line_detected = r_data.get("red_line_detected", False)
                red_line_box = r_data.get("red_line_box", [])  # [x1, y1, x2, y2]

        # 核心判斷邏輯
        if car_count > 0 and red_line_detected and red_line_box:
            overlap_count = 0
            for car in car_boxes:
                # 取得該車的座標框
                c_box = yolo_to_bbox(car['box'], img_w, img_h)
                logger.info(c_box)
                # 計算重疊
                if check_intersection(c_box, red_line_box):
                    overlap_count += 1

            if overlap_count > 0:
                is_violation = True
                status_msg = f"VIOLATION: {overlap_count} Car{'s' if overlap_count > 1 else ''} overlap with Red Line!"
            else:
                status_msg = "Safe: Car detected but not on Red Line"

        elif car_count > 0:
            status_msg = "Safe: Car detected, No Red Line"
        elif red_line_detected:
            status_msg = "Safe: Red Line detected, No Cars"
        else:
            status_msg = "Safe: Clear"

    except Exception as e:
        print(f"Error: {e}")
        status_msg = "System Error"

    log_id = 0

    if is_violation:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_path = f"static/uploads/{timestamp}_evidence.jpg"
        shutil.copy(LIVE_IMG_PATH, evidence_path)

        with SessionLocal() as db:
            new_log = ParkingViolationLog(
                image_path=evidence_path,
                is_violation=True,
                car_detected=True,
                status=status_msg
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)
            log_id = new_log.id
            print(f"違規存檔: {evidence_path}")

    timestamp_now = datetime.now().isoformat()
    latest_cache = {
        "id": log_id,
        "timestamp": timestamp_now,
        "is_violation": is_violation,
        "car_detected": (car_count > 0),
        "status": status_msg,
        "image_url": f"/static/{LIVE_IMG_FILENAME}?t={datetime.now().timestamp()}"
    }
    return is_violation, status_msg


@app.post("/api/upload_form")
async def upload_form(file: UploadFile = File(...)):
    with open(LIVE_IMG_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img_w, img_h = 640, 480
    try:
        with Image.open(LIVE_IMG_PATH) as img:
            img_w, img_h = img.size
    except Exception as e:
        print(f"Warning: Cannot read image size, using default 640x480. Error: {e}")

    is_violation, status_msg = detect_parking(img_w, img_h)

    return {
        "status": "processed",
        "violation_detected": is_violation,
        "message": status_msg,
        "image_url": latest_cache["image_url"]
    }


active_transmissions = {}


@app.post("/api/upload")
async def upload_chunk(
        request: Request,
        background_tasks: BackgroundTasks,
        offset: int = Query(...),
        total: int = Query(...),
        width: int = Query(320),
        height: int = Query(240)
):
    client_ip = request.client.host

    try:
        # 1. 安全讀取數據
        chunk_data = await request.body()
    except ClientDisconnect:
        logger.warning(f"Client {client_ip} disconnected prematurelly.")
        return {"status": "error", "message": "Disconnected"}

    # 2. 初始化或取得緩衝區
    if client_ip not in active_transmissions or offset == 0:
        active_transmissions[client_ip] = bytearray(total)
        logger.info(f"New upload from {client_ip}, total size: {total}")

    # 3. 寫入片段
    buffer = active_transmissions[client_ip]
    end_index = offset + len(chunk_data)

    # 防止 offset 溢出導致 Crash
    if end_index > total:
        return {"status": "error", "message": "Data overflow"}

    buffer[offset:end_index] = chunk_data

    # 4. 檢查是否完成
    if end_index >= total:
        logger.info(f"Image complete ({width}x{height}) from {client_ip}")
        try:
            # 使用解碼函式
            img = decode_rgb565(buffer, width, height)
            img.save(LIVE_IMG_PATH)

            # 清理記憶體
            del active_transmissions[client_ip]
            background_tasks.add_task(detect_parking, width, height)
            return {"status": "complete", "message": "Saved successfully", "command": "ring", "value": "true"}
        except Exception as e:
            logger.error(f"Decode failed: {e}")
            if client_ip in active_transmissions:
                del active_transmissions[client_ip]
            return {"status": "error", "message": str(e)}

    return {"status": "chunk_received", "progress": f"{int(end_index / total * 100)}%"}


@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    logs = db.query(ParkingViolationLog) \
        .filter(ParkingViolationLog.is_violation == True) \
        .order_by(ParkingViolationLog.id.desc()) \
        .all()

    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "timestamp": log.timestamp,
            "status": log.status,
            "image_url": f"/{log.image_path}"
        })
    return results


@app.get("/api/dashboard/latest")
def get_latest_data(db: Session = Depends(get_db)):
    if latest_cache["timestamp"] is not None:
        return latest_cache

    latest = db.query(ParkingViolationLog).order_by(ParkingViolationLog.id.desc()).first()
    if not latest:
        return {"error": "No data"}

    return {
        "id": latest.id,
        "timestamp": latest.timestamp,
        "is_violation": latest.is_violation,
        "car_detected": latest.car_detected,
        "status": f"[History] {latest.status}",
        "image_url": f"/{latest.image_path}"
    }
