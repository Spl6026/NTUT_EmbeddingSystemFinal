import requests
import os
import math
import time
import random

URL = 'http://127.0.0.1:8000/api/upload'

WIDTH = 320
HEIGHT = 240
BYTES_PER_PIXEL = 2
TOTAL_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL

CHUNK_SIZE = 4096 

def create_dummy_image():
    print(f"產生虛擬影像: {WIDTH}x{HEIGHT} (RGB565), 大小: {TOTAL_SIZE} bytes")
    return os.urandom(TOTAL_SIZE)

def run_simulation():
    raw_data = create_dummy_image()
    
    offset = 0
    total_chunks = math.ceil(TOTAL_SIZE / CHUNK_SIZE)
    chunk_idx = 0

    print(f"開始模擬上傳 (共 {total_chunks} 個分片)...")
    start_time = time.time()

    while offset < TOTAL_SIZE:
        chunk = raw_data[offset : offset + CHUNK_SIZE]

        params = {
            "offset": offset,
            "total": TOTAL_SIZE,
            "width": WIDTH,
            "height": HEIGHT
        }

        try:
            response = requests.post(URL, params=params, data=chunk)

            if response.status_code == 200:
                resp_json = response.json()
                chunk_idx += 1
                
                progress = int((offset / TOTAL_SIZE) * 20)
                bar = "#" * progress + "-" * (20 - progress)
                print(f"\r[{bar}] Chunk {chunk_idx}/{total_chunks} | {resp_json.get('status')}", end="")

                if resp_json.get("status") == "complete":
                    print("上傳完成！")
                    print(f"Server 回應: {resp_json['message']}")
                    break
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break

        except Exception as e:
            print(f"連線失敗: {e}")
            break

        offset += len(chunk)
        
        time.sleep(0.01)

    duration = time.time() - start_time
    print(f"總耗時: {duration:.2f} 秒")

if __name__ == "__main__":
    try:
        while True:
            run_simulation()
            print("等待下一輪...", end="")
            for i in range(30, 0, -1):
                print(f"\r下次上傳還有: {i} 秒  ", end="")
                time.sleep(1)
            print("\r" + " " * 30 + "\r", end="")
            
    except KeyboardInterrupt:
        print("程式已手動停止")