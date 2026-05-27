import time
import cv2
import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.geometry_msgs.msg.dds_ import PointStamped_

print("Initializing robot connection...")

ChannelFactoryInitialize(0, "eth0")

client = SportClient()
client.SetTimeout(10.0)
client.Init()

# 📸 kamera init
video_client = VideoClient()
video_client.SetTimeout(1.0)
video_client.Init()

# =========================
# LIDAR OBSTACLE DETECTION
# =========================
obstacle_distance_front = float('inf')

def lidar_range_handler(msg: PointStamped_):
    """Callback ukládající vzdálenost překážky z LiDARu (bez výpisů)"""
    global obstacle_distance_front
    obstacle_distance_front = msg.point.x

# Inicializace odběratele DDS tématu
lidar_sub = ChannelSubscriber("rt/utlidar/range_info", PointStamped_)
lidar_sub.Init(lidar_range_handler, 10)

print("Robot connection ready")

# =========================
# ROUTES
# =========================

ROUTES = {
    "A = forward": ["forward"],
    "B = backward": ["backward"],
    "C = left": ["left"],
    "D = right": ["right"]
}

# =========================
# CAMERA FUNCTION
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
# AGENT (OPRAVENO: POKRAČUJE V CYKLU, NEUKONČUJE FUNKCI PŘEDČASNĚ)
# =========================

def agent(user_input):
    parts = user_input.upper().strip().split()

    if not parts:
        return []

    if "STOP" in parts:
        return ["stop"]

    full_route = []
    
    for part in parts:
        if part == "PICTURE":
            take_picture()
            continue # OPRAVA: continue místo return [] -> nepřeruší rozjetou sekvenci

        if part in ROUTES:
            full_route.extend(ROUTES[part])
        else:
            print(f"[AGENT] Unknown route: {part}")
            # OPRAVA: místo okamžitého returnu ignorujeme neplatný znak a nesmažeme zbytek trasy
            
    return full_route

# =========================
# ROBOT CONTROL
# =========================

def forward(seconds=3):
    global obstacle_distance_front
    print("[ROBOT] MOVE FORWARD")

    # Ochrana: počkáme 0.1s, než se po startu příkazu ustálí data v proměnné z LiDARu
    time.sleep(0.1)

    t0 = time.time()

    while time.time() - t0 < seconds:
        # Tvoje původní podmínka - přidán pouze filtr na extrémně nízké chybové hodnoty/šumy (blízko nule)
        if 0.05 < obstacle_distance_front <= 0.70:
            print(f"🛑 [LIDAR] Detekována překážka v limitní zóně ({obstacle_distance_front:.2f} m). Zastavuji!")
            take_picture()
            break

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