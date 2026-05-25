import time
import cv2
import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient

print("Initializing robot connection...")

ChannelFactoryInitialize(0, "eth0")

client = SportClient()
client.SetTimeout(10.0)
client.Init()

# 📸 kamera init (DOPLNĚNO)
video_client = VideoClient()
video_client.SetTimeout(1.0)
video_client.Init()

print("Robot connection ready")

# =========================
# ROUTES
# =========================

ROUTES = {
    "A": ["forward"],
    "B": ["backward"],
    "C": ["left"],
    "D": ["right"]
}

# =========================
# CAMERA FUNCTION (DOPLNĚNO)
# =========================

def take_picture():
    print("[CAMERA] Taking picture...")

    code, data = video_client.GetImageSample()

    if code != 0:
        print("❌ Camera error:", code)
        return

    if not data:
        print("❌ No data")
        return

    try:
        img_bytes = bytes(data)

        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ Decode failed")
            return

        filename = "image.jpg"
        cv2.imwrite(filename, img)

        print("✅ Saved image.jpg")
        print("scp unitree@ROBOT_IP:~/image.jpg .")

    except Exception as e:
        print("❌ Error:", e)

# =========================
# AGENT
# =========================

def agent(user_input):
    user_input = user_input.upper().strip()

    if user_input == "STOP":
        return ["stop"]

    # 📸 PŘIDÁNO PICTURE
    if user_input == "PICTURE":
        take_picture()
        return []

    if user_input in ROUTES:
        return ROUTES[user_input]

    print("[AGENT] Unknown route")
    return ["stop"]

# =========================
# ROBOT CONTROL (FIXED)
# =========================

def forward(seconds=3):
    print("[ROBOT] MOVE FORWARD")

    t0 = time.time()

    while time.time() - t0 < seconds:
        client.Move(0.6, 0.0, 0.0)
        time.sleep(0.05)

    client.StopMove()


def backward(seconds=2):
    print("[ROBOT] MOVE BACKWARD")

    t0 = time.time()

    while time.time() - t0 < seconds:
        client.Move(-0.6, 0.0, 0.0)
        time.sleep(0.05)

    client.StopMove()


def left(seconds=3.5):
    print("[ROBOT] TURN LEFT")

    t0 = time.time()

    while time.time() - t0 < seconds:
        client.Move(0.0, 0.0, 0.6)
        time.sleep(0.05)

    client.StopMove()


def right(seconds=3.5):
    print("[ROBOT] TURN RIGHT")

    t0 = time.time()

    while time.time() - t0 < seconds:
        client.Move(0.0, 0.0, -0.6)
        time.sleep(0.05)

    client.StopMove()


def stop():
    print("[ROBOT] STOP")
    client.StopMove()

# =========================
# EXECUTOR
# =========================

def execute(route):
    print("[EXECUTOR] Starting route")

    for step in route:

        if step == "forward":
            forward()

        elif step == "backward":
            backward()

        elif step == "left":
            left()

        elif step == "right":
            right()

        elif step == "stop":
            stop()

        else:
            print("[EXECUTOR] Unknown action:", step)

        time.sleep(0.5)

    print("[EXECUTOR] Route complete")

# =========================
# MAIN
# =========================

def main():
    print("\nRobot Dog System Ready\n")

    print("Available routes:")
    for r in ROUTES:
        print("-", r)
    print("- STOP")
    print("- PICTURE\n")

    print("Standing up robot...")
    client.StandUp()
    time.sleep(2)

    while True:
        user_input = input("> ")

        route = agent(user_input)

        print("[MAIN] Selected route:", route)

        execute(route)

        print("\n--- DONE ---\n")


if __name__ == "__main__":
    main()