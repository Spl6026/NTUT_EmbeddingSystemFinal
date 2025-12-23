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
        cmd
    )

    time.sleep(2)  # 等 tunnel 建立
    if proc.poll() is not None:
        print(f"SSH Tunnel failed to start with return code {proc.returncode}")
    else:
        print(f"SSH Tunnel started with PID {proc.pid}")
        
    return proc
