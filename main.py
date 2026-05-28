import time
import cv2
import numpy as np
import threading
import re

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.go2.sport.sport_client import SportClient
from unitree_sdk2py.go2.video.video_client import VideoClient
from unitree_sdk2py.idl.geometry_msgs.msg.dds_ import PointStamped_

print("Inicializace připojení k robotovi...")

ChannelFactoryInitialize(0, "eth0")

client = SportClient()
client.SetTimeout(10.0)
client.Init()

video_client = VideoClient()
video_client.SetTimeout(1.0)
video_client.Init()

# =========================
# LIDAR (vláknově bezpečný)
# =========================
lock = threading.Lock()
obstacle_distance_front = float('inf')

def lidar_range_handler(msg: PointStamped_):
    global obstacle_distance_front
    with lock:
        obstacle_distance_front = msg.point.x

lidar_sub = ChannelSubscriber("rt/utlidar/range_info", PointStamped_)
lidar_sub.Init(lidar_range_handler, 10)

print("Připojení k robotovi je připraveno")

# =========================
# ROUTES (PŘIDÁN OBRAZOVÝ PŘÍKAZ DO MAPOVÁNÍ)
# =========================
ROUTES = {
    "A": "forward",
    "B": "backward",
    "C": "left",
    "D": "right",
    "SPIN": "spin",
    "LIE": "lie",
    "STAND": "stand",
    "PICTURE": "picture"  # Přidáno pro sekvenční zpracování
}

# =========================
# KAMERA
# =========================
def take_picture():
    print("[KAMERA] Pořizování snímku...")

    code, data = video_client.GetImageSample()

    if code != 0 or not data:
        print("❌ Chyba kamery")
        return

    try:
        img_array = np.frombuffer(bytes(data), dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ Dekódování selhalo")
            return

        cv2.imwrite("image.jpg", img)
        print("✅ Snímek uložen jako image.jpg")

    except Exception as e:
        print("❌ Chyba:", e)

# =========================
# AGENT
# =========================
def agent(user_input):
    parts = user_input.upper().strip().split()

    if not parts:
        return []

    if "HELP" in parts:
        print("\n" + "="*50)
        print(" 📖 NÁPOVĚDA K OVLÁDÁNÍ ROBOTA")
        print("="*50)
        print(" Příkazy můžeš řetězit za sebe (např: A5 C2 PICTURE B3 LIE)")
        print("-"*50)
        print(" 🏃 POHYBY (lze přidat čas v sekundách, např. A5 nebo C2.5):")
        print("   A [sekundy]    - Pohyb VPŘED (výchozí 3.0s)")
        print("   B [sekundy]    - Pohyb VZAD (výchozí 3.0s)")
        print("   C [sekundy]    - Krok VLEVO (výchozí 3.6s)")
        print("   D [sekundy]    - Krok VPRAVO (výchozí 3.3s)")
        print("   SPIN [sekundy] - Otočení na místě (výchozí 7.5s)")
        print("\n 🤖 POLOHY A SPECIÁLNÍ AKCE:")
        print("   STAND          - Robot se postaví")
        print("   LIE            - Robot si lehne")
        print("   PICTURE        - Vyfocení snímku (provede se v zadaném pořadí)")
        print("   STOP           - Okamžité zastavení motorů")
        print("   HELP           - Zobrazí tuto nápovědu")
        print("="*50 + "\n")
        return []

    if "STOP" in parts:
        return [("stop", None)]

    route = []

    for part in parts:
        # ODSTRANĚNO: Okamžité focení uvnitř agenta

        match = re.match(r"^([A-Z]+)(\d+(?:\.\d+)?)?$", part)
        
        if match:
            cmd_letter = match.group(1)
            duration_str = match.group(2)
            
            if cmd_letter in ROUTES:
                duration = float(duration_str) if duration_str else None
                route.append((ROUTES[cmd_letter], duration))
            else:
                print("[AGENT] Neznámý příkaz:", cmd_letter)
        else:
            print("[AGENT] Neplatný formát:", part)

    return route

# =========================
# BEZPEČNÝ POHYB (JÁDRO)
# =========================
def move(vx, vy, vyaw, duration):
    t0 = time.time()

    while time.time() - t0 < duration:
        client.Move(vx, vy, vyaw)
        time.sleep(0.02)

    client.StopMove()

# =========================
# POHYBY
# =========================
def forward(seconds=3):
    print(f"[ROBOT] VPŘED ({seconds}s)")

    t0 = time.time()

    while time.time() - t0 < seconds:

        with lock:
            dist = obstacle_distance_front

        if 0.05 < dist <= 0.50:
            print(f"🛑 Překážka: {dist:.2f} m")
            client.StopMove()
            take_picture()
            return False

        client.Move(0.6, 0.0, 0.0)
        time.sleep(0.02)

    client.StopMove()
    return True


def backward(seconds=3):
    print(f"[ROBOT] VZAD ({seconds}s)")
    move(-0.6, 0.0, 0.0, seconds)
    return True


def left(seconds=3.6):
    print(f"[ROBOT] VLEVO ({seconds}s)")
    move(0.0, 0.0, 0.6, seconds)
    return True


def right(seconds=3.3):
    print(f"[ROBOT] VPRAVO ({seconds}s)")
    move(0.0, 0.0, -0.6, seconds)
    return True


def spin(seconds=7.5):
    print(f"[ROBOT] OTOČENÍ ({seconds}s)")
    move(0.0, 0.0, 1, seconds)
    return True

# =========================
# POLOHY
# =========================
def lie():
    print("[ROBOT] LEHNOUT")

    try:
        client.StopMove()
        time.sleep(0.2)
        client.StandDown()
    except Exception as e:
        print("❌ Chyba při lehání (StandDown):", e)


def stand():
    print("[ROBOT] POSTAVIT SE")

    try:
        client.StandUp()
    except Exception as e:
        print("❌ Chyba při vstávání (StandUp):", e)

# =========================
# ZASTAVENÍ
# =========================
def stop():
    print("[ROBOT] ZASTAVIT")
    client.StopMove()

# =========================
# EXEKUTOR (UPRAVENO PRO SEKVENČNÍ FOCENÍ)
# =========================
def execute(route):
    if not route:
        return

    print("[EXEKUTOR] Spouštění trasy")

    for step, duration in route:

        client.Move(0.0, 0.0, 0.0)
        time.sleep(0.05)
        client.StopMove()
        time.sleep(0.05)

        kwargs = {}
        if duration is not None:
            kwargs['seconds'] = duration

        success = True

        if step == "forward":
            success = forward(**kwargs)
        elif step == "backward":
            success = backward(**kwargs)
        elif step == "left":
            success = left(**kwargs)
        elif step == "right":
            success = right(**kwargs)
        elif step == "spin":
            success = spin(**kwargs)
        elif step == "lie":
            lie()
        elif step == "stand":
            stand()
        elif step == "picture":  # Focení se spustí až v tomto kroku trasy
            take_picture()
        elif step == "stop":
            stop()

        if not success:
            print("⚠️ Trasa PŘERUŠENA kvůli překážce! Zbývající příkazy zrušeny.")
            break

        time.sleep(0.2)

    print("[EXEKUTOR] Zpracování trasy dokončeno")

# =========================
# ZAHŘÁTÍ
# =========================
def warmup():
    print("Zahřívání řídicího kanálu...")

    for _ in range(5):
        client.Move(0.0, 0.0, 0.0)
        time.sleep(0.05)

    client.StopMove()
    time.sleep(1)

# =========================
# HLAVNÍ PROGRAM
# =========================
def main():
    print("\nSystém robotického psa je připraven\n")

    print("Robot se staví...")
    client.StandUp()
    time.sleep(3)

    warmup()

    print("Připraveno.")
    print("Pro výpis všech příkazů napište HELP.")

    while True:
        user_input = input("> ")

        route = agent(user_input)

        if route:
            print("[HLAVNÍ] Trasa:", route)
            execute(route)
            print("\n--- HOTOVO ---\n")


if __name__ == "__main__":
    main()