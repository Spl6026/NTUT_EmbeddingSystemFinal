import shutil
from contextlib import asynccontextmanager
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
from PIL import Image, ImageDraw
import numpy as np
from ssh_tunnel import start_ssh_tunnel
import config
import state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System Starting...")

    state.ssh_proc = start_ssh_tunnel()

    if state.ssh_proc:
        logger.info(f"SSH Tunnel active (PID: {state.ssh_proc.pid})")
    else:
        logger.error("SSH Tunnel failed!")

    yield

    logger.info("System Shutting down...")
    if state.ssh_proc:
        state.ssh_proc.terminate()
        try:
            state.ssh_proc.wait(timeout=3)
        except:
            state.ssh_proc.kill()
        logger.info("SSH Tunnel closed.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


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


def draw_violation_boxes(input_path, output_path, car_boxes, red_line_boxes):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)

            for r_box in red_line_boxes:
                if r_box and len(r_box) == 4:
                    box = [int(c) for c in r_box]
                    draw.rectangle(box, outline="red", width=5)

            for car in car_boxes:
                if len(car) == 4:
                    box = [int(c) for c in car]
                    draw.rectangle(box, outline="blue", width=3)

            img.save(output_path, quality=95)
            logger.info(f"Evidence saved: {output_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to draw boxes: {e}")
        try:
            shutil.copy(input_path, output_path)
        except:
            pass
        return False


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
    logger.info(f"Image size: {img_w}x{img_h}")
    car_count = 0
    car_boxes = []
    red_line_detected = False
    red_line_boxes = []
    is_violation = False
    status_msg = "Analyzing..."
    try:
        with open(config.LIVE_IMG_PATH, 'rb') as f:
            img_bytes = f.read()
    except FileNotFoundError:
        return False, "Error: Image not found"

    try:
        # 呼叫車輛模型
        resp_veh = requests.post(config.VEHICLE_API_URL,
                                 files={'image': ('live.jpg', img_bytes, 'image/jpeg')},
                                 data={'model': 'yolov13n'}, timeout=20)
        if resp_veh.status_code == 200:
            v_data = resp_veh.json()
            # logging.info(f"Vehicle detected: {v_data}")
            detections = v_data.get("detections", [])
            for det in detections:
                if det.get("class_name") == "car":
                    car_boxes.append(det["bbox"])

            car_count = len(car_boxes)
            logging.info(f"Cars detected: {car_count}")

        # 呼叫紅線模型
        resp_red = requests.post(config.REDLINE_API_URL,
                                 files={'image': ('live.jpg', img_bytes, 'image/jpeg')},
                                 data={'model': 'yolov11m-seg'}, timeout=20)
        if resp_red.status_code == 200:
            r_data = resp_red.json()
            # logging.info(f"Red line detected: {r_data}")
            segments = r_data.get("segments", [])

            for seg in segments:
                if "red" in seg.get("class_name", "").lower():
                    red_line_detected = True
                    red_line_boxes.append(seg.get("bbox"))

            red_line_count = len(red_line_boxes)
            logging.info(f"Red line detected: {red_line_count}")

        draw_violation_boxes(
            config.LIVE_IMG_PATH,
            config.LIVE_IMG_PATH,
            car_boxes,
            red_line_boxes
        )
        # 核心判斷邏輯
        if car_count > 0 and red_line_detected:
            overlap_count = 0
            for c_box in car_boxes:
                car_hit_line = False
                for r_box in red_line_boxes:
                    if check_intersection(c_box, r_box):
                        car_hit_line = True
                        break

                if car_hit_line:
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
        shutil.copy(config.LIVE_IMG_PATH, evidence_path)

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
    state.latest_cache = {
        "id": log_id,
        "timestamp": timestamp_now,
        "is_violation": is_violation,
        "car_detected": (car_count > 0),
        "status": status_msg,
        "image_url": f"/static/{config.LIVE_IMG_FILENAME}?t={datetime.now().timestamp()}"
    }
    return is_violation, status_msg


@app.post("/api/upload_form")
async def upload_form(file: UploadFile = File(...)):
    with open(config.LIVE_IMG_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    img_w, img_h = 640, 480
    try:
        with Image.open(config.LIVE_IMG_PATH) as img:
            img_w, img_h = img.size
    except Exception as e:
        print(f"Warning: Cannot read image size, using default 640x480. Error: {e}")

    is_violation, status_msg = detect_parking(img_w, img_h)

    return {
        "status": "processed",
        "violation_detected": is_violation,
        "message": status_msg,
        "image_url": state.latest_cache["image_url"]
    }


@app.get("/api/system/status")
def get_system_status():
    tunnel_active = state.ssh_proc.poll() is None
    return {
        "status": "online",
        "tunnel_active": tunnel_active,
        "tunnel_pid": state.ssh_proc.pid if tunnel_active else None,
        "timestamp": datetime.now().isoformat()
    }


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
    if client_ip not in state.active_transmissions or offset == 0:
        state.active_transmissions[client_ip] = bytearray(total)
        logger.info(f"New upload from {client_ip}, total size: {total}")

    # 3. 寫入片段
    buffer = state.active_transmissions[client_ip]
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
            img.save(config.LIVE_IMG_PATH)

            # 清理記憶體
            del state.active_transmissions[client_ip]
            background_tasks.add_task(detect_parking, width, height)
            return {"status": "complete", "message": "Saved successfully", "command": "ring", "value": "true"}
        except Exception as e:
            logger.error(f"Decode failed: {e}")
            if client_ip in state.active_transmissions:
                del state.active_transmissions[client_ip]
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
    if state.latest_cache["timestamp"] is not None:
        return state.latest_cache

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
