import time
import cv2
import numpy as np
import threading
import re  # Přidán import pro regulární výrazy

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.geometry_msgs.msg.dds_ import PointStamped_

print("Initializing robot connection...")

ChannelFactoryInitialize(0, "eth0")

client = SportClient()
client.SetTimeout(10.0)
client.Init()

video_client = VideoClient()
video_client.SetTimeout(1.0)
video_client.Init()

# =========================
# LIDAR (thread-safe)
# =========================
lock = threading.Lock()
obstacle_distance_front = float('inf')

def lidar_range_handler(msg: PointStamped_):
    global obstacle_distance_front
    with lock:
        obstacle_distance_front = msg.point.x

lidar_sub = ChannelSubscriber("rt/utlidar/range_info", PointStamped_)
lidar_sub.Init(lidar_range_handler, 10)

print("Robot connection ready")

# =========================
# ROUTES (Zjednodušeno na mapování 1:1)
# =========================
ROUTES = {
    "A": "forward",
    "B": "backward",
    "C": "left",
    "D": "right",
    "SPIN": "spin",
    "LIE": "lie",
    "STAND": "stand"
}

# =========================
# CAMERA
# =========================
def take_picture():
    print("[CAMERA] Taking picture...")

    code, data = video_client.GetImageSample()

    if code != 0 or not data:
        print("❌ Camera error")
        return

    try:
        img_array = np.frombuffer(bytes(data), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ Decode failed")
            return

        cv2.imwrite("image.jpg", img)
        print("✅ Saved image.jpg")

    except Exception as e:
        print("❌ Error:", e)

# =========================
# AGENT (UPRAVENO PRO PARSOVÁNÍ ČÍSEL)
# =========================
def agent(user_input):
    parts = user_input.upper().strip().split()

    if not parts:
        return []

    if "STOP" in parts:
        return [("stop", None)]

    route = []

    for part in parts:
        if part == "PICTURE":
            take_picture()
            continue

        # Regulární výraz: hledá písmena na začátku a volitelná čísla (i desetinná) na konci
        match = re.match(r"^([A-Z]+)(\d+(?:\.\d+)?)?$", part)
        
        if match:
            cmd_letter = match.group(1)   # Např. "A" nebo "SPIN"
            duration_str = match.group(2) # Např. "5" nebo "2.5" nebo None
            
            if cmd_letter in ROUTES:
                # Pokud číslo zadáno není, předáme None (použije se výchozí čas funkce)
                duration = float(duration_str) if duration_str else None
                route.append((ROUTES[cmd_letter], duration))
            else:
                print("[AGENT] Unknown command:", cmd_letter)
        else:
            print("[AGENT] Invalid format:", part)

    return route

# =========================
# SAFE MOVE CORE (BEZ ZMĚN)
# =========================
def move(vx, vy, vyaw, duration):
    t0 = time.time()

    while time.time() - t0 < duration:
        client.Move(vx, vy, vyaw)
        time.sleep(0.02)

    client.StopMove()

# =========================
# MOVES (ZŮSTÁVAJÍ VÝCHOZÍ ČASY)
# =========================
def forward(seconds=3):
    print(f"[ROBOT] FORWARD ({seconds}s)")

    t0 = time.time()

    while time.time() - t0 < seconds:

        with lock:
            dist = obstacle_distance_front

        if 0.05 < dist <= 0.50:
            print(f"🛑 Obstacle: {dist:.2f} m")
            take_picture()
            break

        client.Move(0.6, 0.0, 0.0)
        time.sleep(0.02)

    client.StopMove()


def backward(seconds=3):
    print(f"[ROBOT] BACKWARD ({seconds}s)")
    move(-0.6, 0.0, 0.0, seconds)


def left(seconds=3.5):
    print(f"[ROBOT] LEFT ({seconds}s)")
    move(0.0, 0.0, 0.6, seconds)


def right(seconds=3.5):
    print(f"[ROBOT] RIGHT ({seconds}s)")
    move(0.0, 0.0, -0.6, seconds)


def spin(seconds=7.5):
    print(f"[ROBOT] SPIN ({seconds}s)")
    move(0.0, 0.0, 1, seconds)

# =========================
# POSTURES
# =========================
def lie():
    print("[ROBOT] LIE DOWN")

    try:
        client.StopMove()
        time.sleep(0.2)
        client.StandDown()
    except Exception as e:
        print("❌ StandDown (lie) error:", e)


def stand():
    print("[ROBOT] STAND")

    try:
        client.StandUp()
    except Exception as e:
        print("❌ StandUp error:", e)

# =========================
# STOP
# =========================
def stop():
    print("[ROBOT] STOP")
    client.StopMove()

# =========================
# EXECUTOR (UPRAVENO PRO PŘIJÍMÁNÍ ČASU)
# =========================
def execute(route):
    print("[EXECUTOR] Starting route")

    for step, duration in route:

        client.Move(0.0, 0.0, 0.0)
        time.sleep(0.05)
        client.StopMove()
        time.sleep(0.05)

        # Příprava argumentů pro funkci - pokud trvání existuje, pošleme ho dál
        kwargs = {}
        if duration is not None:
            kwargs['seconds'] = duration

        if step == "forward":
            forward(**kwargs)
        elif step == "backward":
            backward(**kwargs)
        elif step == "left":
            left(**kwargs)
        elif step == "right":
            right(**kwargs)
        elif step == "spin":
            spin(**kwargs)
        elif step == "lie":
            lie()
        elif step == "stand":
            stand()
        elif step == "stop":
            stop()

        time.sleep(0.2)

    print("[EXECUTOR] Route complete")

# =========================
# WARMUP (BEZ ZMĚN)
# =========================
def warmup():
    print("Warming up control channel...")

    for _ in range(5):
        client.Move(0.0, 0.0, 0.0)
        time.sleep(0.05)

    client.StopMove()
    time.sleep(1)

# =========================
# MAIN
# =========================
def main():
    print("\nRobot Dog System Ready\n")

    print("Standing up robot...")
    client.StandUp()
    time.sleep(3)

    warmup()

    print("Ready.")

    while True:
        user_input = input("> ")

        route = agent(user_input)

        print("[MAIN] Route parsing completed:", route)
        execute(route)

        print("\n--- DONE ---\n")


if __name__ == "__main__":
    main()