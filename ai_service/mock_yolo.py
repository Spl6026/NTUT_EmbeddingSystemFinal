import uvicorn
import random
import time
from fastapi import FastAPI, UploadFile, File

app = FastAPI()


# 模擬模型 A
@app.post("/predict/vehicle")
async def predict_vehicle(file: UploadFile = File(...)):
    print(f"AI Service (Vehicle): 正在分析車輛... {file.filename}")
    time.sleep(random.uniform(0.2, 0.5))
    car_count = random.choices([0, 1, 2, 3], weights=[0.2, 0.5, 0.2, 0.1])[0]
    boxes = []
    for _ in range(car_count):
        w = random.uniform(0.15, 0.30)
        h = random.uniform(0.15, 0.25)

        # 50% 機率違規，50% 機率安全
        is_violation_attempt = random.choice([True, False])

        if is_violation_attempt:
            # 違規模式
            # 紅線在 y=0.83 附近
            yc = random.uniform(0.75, 0.90)
            xc = random.uniform(w / 2, 1.0 - w / 2)
        else:
            # 安全模式
            yc = random.uniform(h / 2, 0.60)
            xc = random.uniform(w / 2, 1.0 - w / 2)

        boxes.append({
            "box": [xc, yc, w, h],
            "confidence": random.uniform(0.8, 0.99)
        })

    return {
        "model": "YOLO",
        "car_count": car_count,
        "boxes": boxes
    }

# 模擬模型 B
@app.post("/predict/redline")
async def predict_redline(file: UploadFile = File(...)):
    print(f"AI (RedLine): 分析中...")
    time.sleep(random.uniform(0.1, 0.3))

    has_red_line = random.random() > 0.2

    red_line_box = []
    if has_red_line:
        # [x1, y1, x2, y2]
        red_line_box = [0, 400, 640, 480]

    return {
        "model": "RedLine-Seg",
        "red_line_detected": has_red_line,
        "red_line_box": red_line_box
    }

if __name__ == "__main__":
    print("AI Service Started on port 5000...")
    uvicorn.run(app, host="0.0.0.0", port=5000)