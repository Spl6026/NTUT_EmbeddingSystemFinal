import requests
import time
import random

url = 'http://127.0.0.1:8000/api/detect_parking'


def create_dummy_image():
    with open("test_image.jpg", "wb") as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
    return "test_image.jpg"


def run_simulation():
    print("開始模擬 Pico 上傳...")

    img_path = create_dummy_image()

    try:
        with open(img_path, 'rb') as f:
            files = {'file': f}
            print(f"正在上傳 {img_path} 到 {url} ...")
            response = requests.post(url, files=files)

        if response.status_code == 200:
            data = response.json()
            print("上傳成功！伺服器回應：")
            print(f"   - 資料: {data}")
        else:
            print(f"伺服器錯誤: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"連線失敗: {e}")
        print("請檢查 Uvicorn 是否有啟動？")


if __name__ == "__main__":
    run_simulation()