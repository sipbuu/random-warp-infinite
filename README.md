[![logo](https://i.imgur.com/OU4bpcy.png)](https://github.com/sipbuu/random-warp-infinite/releases/tag/v1.0)

# Random Warp — 20w14∞ (Complete Overhaul) 

Teleports all players to a randomly generated dimension on a set interval, with a bossbar countdown. Built for **Minecraft Java 20w14infinite** on a locally hosted server.

---

## How it works

Uses **RCON** (Minecraft's built-in remote console) to send commands directly to the server, no window focus tricks, no previous keyboard simulation. Fully works minimized or in the background.

Two versions are included:

| File | Description |
|---|---|
| `randomwarp_gui.exe` | GUI app with live log, countdown, config fields |
| `randomwarp.exe` | CLI version, same functionality |
| `randomwarp_gui.py` | .py version of the corresponding .exe |
| `randomwarp.py` | .py version of the corresponding .exe |
---

## Setup 

### 1. Enable RCON in `server.properties`

```
enable-rcon=true
rcon.port=25575
rcon.password=yourpassword
```

Restart the server after editing.

### 2. For the CLI version only — edit the config block at the top of `randomwarp.py`

```python
RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASSWORD = "yourpassword"
```

The GUI version lets you enter these in the app directly.

### 3. Install dependencies (if you run the .py files)

```
pip install customtkinter
```

> CLI version (`randomwarp.py`) has no dependencies beyond Python stdlib.

### 4. Run

```
python randomwarp_gui.py
```

or

```
python randomwarp.py
```

---

## Credits

- [Besteres](https://github.com/Besteres) — original RandomWarps20w14 project
- [Sipbuu](https://github.com/sipbuu) — rewrite, RCON approach, GUI