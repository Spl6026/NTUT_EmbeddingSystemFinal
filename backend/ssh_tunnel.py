import subprocess
import time

def start_ssh_tunnel():
    cmd = [
        "ssh",
        "-N",
        "-L", "9000:localhost:8000",
        "vcppx"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)  # 等 tunnel 建立
    return proc
