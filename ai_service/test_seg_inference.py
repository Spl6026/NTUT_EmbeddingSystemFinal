from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

# =========================
# 1. 設定路徑
# =========================
MODEL_PATH = "runs/segment/rlmd_yolov11m_seg_transfer2/weights/best.pt"   # 你的權重
IMAGE_PATH = "test3.jpg"         # 測試圖片
OUTPUT_PATH = "output_masked.jpg"

# =========================
# 2. 載入模型
# =========================
model = YOLO(MODEL_PATH)

print("Model loaded.")
print("Classes:", model.names)

# =========================
# 3. 讀取圖片
# =========================
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

h, w = img.shape[:2]
print(f"Image shape: {w}x{h}")

# =========================
# 4. Inference（segmentation）
# =========================
results = model(
    img,
    conf=0.2,      # 先不要太高
    iou=0.45,
    verbose=True
)

r = results[0]

# =========================
# 5. 檢查是否有 mask
# =========================
if r.masks is None:
    print("❌ No masks detected.")
    exit(0)

print(f"✅ Detected {len(r.masks)} segments")

# =========================
# 6. 畫 mask 疊圖
# =========================
overlay = img.copy()

for i, mask in enumerate(r.masks.data):
    mask_np = mask.cpu().numpy()

    # resize mask to original image size
    mask_resized = cv2.resize(
        mask_np,
        (w, h),
        interpolation=cv2.INTER_NEAREST
    )

    color = np.random.randint(0, 255, size=3).tolist()

    colored_mask = np.zeros_like(img)
    colored_mask[mask_resized > 0.5] = color

    overlay = cv2.addWeighted(overlay, 1.0, colored_mask, 0.5, 0)

    if r.boxes is not None:
        box = r.boxes.xyxy[i].cpu().numpy().astype(int)
        cls_id = int(r.boxes.cls[i])
        conf = float(r.boxes.conf[i])
        label = f"{model.names[cls_id]} {conf:.2f}"

        cv2.rectangle(
            overlay,
            (box[0], box[1]),
            (box[2], box[3]),
            color,
            2
        )
        cv2.putText(
            overlay,
            label,
            (box[0], box[1] - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )


# =========================
# 7. 存檔
# =========================
cv2.imwrite(OUTPUT_PATH, overlay)
print(f"✅ Masked image saved to {OUTPUT_PATH}")
