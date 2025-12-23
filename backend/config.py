import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")

LIVE_IMG_FILENAME = "live.jpg"
LIVE_IMG_PATH = os.path.join(STATIC_DIR, LIVE_IMG_FILENAME)

AI_SERVICE_PORT = 9000
AI_HOST = os.getenv("AI_SERVICE_URL", f"http://localhost:{AI_SERVICE_PORT}")

VEHICLE_API_URL = f"{AI_HOST}/detect"
REDLINE_API_URL = f"{AI_HOST}/segment"

os.makedirs(UPLOAD_DIR, exist_ok=True)