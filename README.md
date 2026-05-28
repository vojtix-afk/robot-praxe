# Go2 Robot Dog Control System

Projekt zaměřený na ovládání robotického psa Unitree Go2 pomocí Pythonu a knihovny `unitree_sdk2py`.

## Funkce

* ovládání pohybu robota pomocí příkazů
* řetězení více příkazů do jedné sekvence
* autonomní zastavení před překážkou pomocí LiDARu
* automatické pořízení fotografie při detekci překážky
* ovládání poloh robota
* práce s kamerou robota

---

# Příklad použití

```text id="rd1"
A5 D2 A3 PICTURE LIE
```

Robot:

1. jde vpřed
2. otočí se
3. pokračuje vpřed
4. pořídí fotografii
5. lehne si

---

# Bezpečnostní logika

Robot využívá LiDAR senzor.

Pokud detekuje překážku:

* zastaví se
* pořídí fotografii
* přeruší aktuální trasu

---

# Použité technologie

* Python
* Unitree SDK (`unitree_sdk2py`)
* OpenCV
* NumPy
* LiDAR
* Unitree Go2

---

# Spuštění

```bash id="rd2"
python3 main.py
```

Po spuštění programu lze zadat příkaz:

```text id="rd3"
HELP
```

který zobrazí všechny dostupné příkazy a jejich použití.