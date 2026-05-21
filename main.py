"""
Robot Dog Project

Simple control system for Unitree Go2.

Features:
- predefined routes
- simple agent logic
- forward / backward / left / right movement
- prepared for future Go2 SDK integration
"""

import time


# =========================
# 1. ROUTES (MAPA CHOVÁNÍ)
# =========================
# Každá trasa představuje sérii kroků,
# které robot vykoná postupně.

ROUTES = {
    "HOME": ["forward", "forward", "left", "forward"],

    "TABLE": ["backward", "right", "forward", "forward"],

    "DOOR": ["left", "backward", "right", "forward"]
}


# =========================
# 2. AGENT (ROZHODOVÁNÍ)
# =========================
# Převádí vstup uživatele na trasu.

def agent(user_input):

    user_input = user_input.upper().strip()

    # Nouzový stop
    if user_input == "STOP":
        return ["stop"]

    # Pokud trasa existuje
    if user_input in ROUTES:
        return ROUTES[user_input]

    # Neznámý vstup
    print("[AGENT] Unknown input -> stopping robot")


    return ["stop"]


# =========================
# 3. ROBOT CONTROLLER
# =========================
# Zatím pouze simulace.
# Později se sem napojí Go2 SDK.

def forward():
    print("[ROBOT] MOVE FORWARD")


def backward():
    print("[ROBOT] MOVE BACKWARD")


def left():
    print("[ROBOT] TURN LEFT")


def right():
    print("[ROBOT] TURN RIGHT")


def stop():
    print("[ROBOT] STOP")


# =========================
# 4. EXECUTOR
# =========================
# Vykonává plán krok po kroku.

def execute(route):

    print("[EXECUTOR] Starting route execution")

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
            print(f"[EXECUTOR] Unknown action: {step}")

        # Pauza mezi příkazy
        time.sleep(1)

    print("[EXECUTOR] Route finished")


# =========================
# 5. MAIN LOOP
# =========================

def main():

    print("Robot Dog System Ready")
    print()

    print("Available routes:")

    for route_name in ROUTES:
        print("-", route_name)

    print("- STOP")
    print()

    while True:

        user_input = input("> ")

        route = agent(user_input)

        print("[MAIN] Selected route:", route)

        execute(route)

        print("\n--- DONE ---\n")


# =========================
# 6. START PROGRAMU
# =========================

if __name__ == "__main__":
    main()