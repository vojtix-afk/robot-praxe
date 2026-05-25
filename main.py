import time

# =========================
# UNITREE SDK IMPORTS
# =========================

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.go2.sport.sport_client import SportClient


# =========================
# INITIALIZATION
# =========================

print("Initializing robot connection...")

# Network interface
# Možná bude potřeba změnit "eth0"
# podle vašeho robota (např. wlan0)

ChannelFactoryInitialize(0, "eth0")

client = SportClient()

client.SetTimeout(10.0)

client.Init()

print("Robot connection ready")


# =========================
# ROUTES
# =========================
# Předdefinované cesty robota

ROUTES = {

    "A": [
        "forward",
        "forward",
        "left",
        "forward"
    ],

    "B": [
        "backward",
        "right",
        "forward"
    ],

    "C": [
        "left",
        "forward",
        "right"
    ]
}


# =========================
# AGENT
# =========================
# Rozhoduje kterou trasu vykonat

def agent(user_input):

    user_input = user_input.upper().strip()

    # Nouzové zastavení
    if user_input == "STOP":
        return ["stop"]

    # Pokud existuje trasa
    if user_input in ROUTES:
        return ROUTES[user_input]

    # Neznámý vstup
    print("[AGENT] Unknown route")

    return ["stop"]


# =========================
# ROBOT MOVEMENT FUNCTIONS
# =========================

def forward():

    print("[ROBOT] MOVE FORWARD")

    # vx, vy, vyaw
    client.Move(0.3, 0.0, 0.0)

    time.sleep(2)

    client.StopMove()


def backward():

    print("[ROBOT] MOVE BACKWARD")

    client.Move(-0.3, 0.0, 0.0)

    time.sleep(2)

    client.StopMove()


def left():

    print("[ROBOT] TURN LEFT")

    client.Move(0.0, 0.0, 0.5)

    time.sleep(1)

    client.StopMove()


def right():

    print("[ROBOT] TURN RIGHT")

    client.Move(0.0, 0.0, -0.5)

    time.sleep(1)

    client.StopMove()


def stop():

    print("[ROBOT] STOP")

    client.StopMove()


# =========================
# EXECUTOR
# =========================
# Vykoná jednotlivé kroky trasy

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

        # Pauza mezi kroky
        time.sleep(1)

    print("[EXECUTOR] Route complete")


# =========================
# MAIN LOOP
# =========================

def main():

    print()
    print("Robot Dog System Ready")
    print()

    print("Available routes:")

    for route_name in ROUTES:
        print("-", route_name)

    print("- STOP")
    print()

    # Postavení robota
    print("Standing up robot...")

    client.StandUp()

    time.sleep(2)

    while True:

        user_input = input("> ")

        route = agent(user_input)

        print("[MAIN] Selected route:", route)

        execute(route)

        print("\n--- DONE ---\n")


# =========================
# START PROGRAMU
# =========================

if __name__ == "__main__":
    main()