import sys
import time
import board
import busio
import digitalio
import binascii
import storage
import wifi
import adafruit_requests
import ssl
import time
import socketpool
import gc
import pwmio
from adafruit_ov7670 import (
    OV7670,
    OV7670_COLOR_RGB,   # <--- 修正這裡：原本是 _RGB565，改成 _RGB
    OV7670_SIZE_DIV2,   # 使用 QQVGA (160x120)
)

POST_URL = "http://10.50.79.127:8000/api/upload"

CIRCUITPY_WIFI_SSID = "tomorin"
CIRCUITPY_WIFI_PASSWORD = "12345678"

# --- 1. WiFi 連線 ---
# --- 1. WiFi 連線 (自動模式) ---
print("Checking WiFi connection...")

# 給系統一點時間自動連線 (通常在啟動時就連好了)
retry_count = 0
while not wifi.radio.ipv4_address and retry_count < 0:
    print("Waiting for auto-connect...")
    time.sleep(1)
    retry_count += 1

if wifi.radio.ipv4_address:
    print(f"Connected! IP: {wifi.radio.ipv4_address}")
else:
    print("Auto-connect failed. Please check settings.toml or WiFi signal.")
    # 如果自動連線失敗，才嘗試最簡化手動連線 (不帶參數名)
    try:
        wifi.radio.connect("tomorin", "12345678")
        print(f"Manual connect success! IP: {wifi.radio.ipv4_address}")
    except Exception as e:
        print(f"Final connection attempt failed: {e}")
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# 1. 設定 I2C
i2c = busio.I2C(scl=board.GP21, sda=board.GP20)

# 2. 初始化 OV7670
cam = OV7670(
    i2c,
    data_pins=[
        board.GP0, board.GP1, board.GP2, board.GP3, 
        board.GP4, board.GP5, board.GP6, board.GP7
    ],
    clock=board.GP14, 
    vsync=board.GP13, 
    href=board.GP12, 
    mclk=board.GP15, 
    shutdown=None, 
    reset=None, 
)

print("Camera init success!")
# print("VSYNC pin:", cam._vsync)
# print("HREF pin:", cam._href)


# 3. 設定參數 (修正這裡)
cam.size = OV7670_SIZE_DIV2
cam.colorspace = OV7670_COLOR_RGB # <--- 修正這裡
cam.flip_y = True
cam.flip_x = True

# 取得長寬 (DIV4 通常是 160x120)
width = cam.width
height = cam.height
TOTAL_SIZE = width * height * 2
print(f"Resolution: {width}x{height}")

# 建立緩衝區 (RGB565 每個像素 2 bytes)
buf = bytearray(2 * width * height)

# 4. 暖機
print("Warming up camera (2s)...")
time.sleep(2)

# 5. 拍照
print("Capturing...")
try:
    print("run")
    cam.capture(buf)
    print("Capture done!")
except Exception as e:
    print(f"Capture failed: {e}")

# 6. 輸出數據
print("\n" + "="*20)
print("---START_HEX_DATA---")


# 輸出 Hex
# hex_str = binascii.hexlify(buf).decode('utf-8')
# chunk_size = 1024 
# for i in range(0, len(hex_str), chunk_size):
#     print(hex_str[i:i+chunk_size], end='')

# print("\n---END_HEX_DATA---")
# print("="*20 + "\n")

# print("Finished. Copy the string above.")

BUZZER_PIN = board.GP16

# 初始化 PWM
pwm = pwmio.PWMOut(
    BUZZER_PIN, 
    frequency=440, # 初始頻率 A4
    duty_cycle=0   
)

def play_alarm(duration=0.2):
    """響一聲短音"""
    pwm.duty_cycle = 2**15
    time.sleep(duration)
    pwm.duty_cycle = 0
    time.sleep(0.2)
    
def upload_in_chunks():
    print("Capturing 320x240...")
    cam.capture(buf)
    
    # 2. 設定每一塊的大小 (例如每次傳 20 行)
    # 320 像素 * 2 bytes * 20 行 = 12800 bytes (約 12.5 KB)
    # 這個大小對於 WiFi 來說非常輕鬆
    chunk_size = width * 2 * 20 
    
    print("Starting chunked upload...")
    for offset in range(0, TOTAL_SIZE, chunk_size):
        # 取得片段的 view，這不會產生新的記憶體拷貝
        chunk = memoryview(buf)[offset : offset + chunk_size]
        
        # 建立帶參數的 URL
        url = f"{POST_URL}?offset={offset}&total={TOTAL_SIZE}&width={width}&height={height}"
        
        try:
            # 拍照後每一段的傳送都需要清理記憶體
            gc.collect() 
            response = requests.post(url, data=chunk)
            print(f"Sent {offset}: {response.status_code}")
            # --- 關鍵：只在最後一個片段檢查回傳值 ---
            if offset + chunk_size >= TOTAL_SIZE:
                if response.status_code == 200:
                    try:
                        res_json = response.json()
                        if res_json.get("command") == "ring":
                            if res_json.get("value") == "true":
                                print("收到後端指令：觸發蜂鳴器！")
                                play_alarm(0.5) # 響 0.5 秒
                    except Exception as e:
                        print("解析回傳 JSON 失敗:", e)

            response.close()
        except Exception as e:
            print(f"Chunk at {offset} failed: {e}")
            break
    
    print("Done!")

# 執行
while True:
    upload_in_chunks()
    time.sleep(10)
    
pwm.deinit()
