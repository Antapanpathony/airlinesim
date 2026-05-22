# ✈ Airline Empire · 1900–2050

> Build your airline from biplane to hypersonic jet — a Python strategy simulation spanning 150 years of aviation history.

---

## Overview

**Airline Empire** is a turn-based airline management game written in Python with a Tkinter GUI. Starting anywhere from 1903 to 2040, you build a global airline from scratch — buying aircraft, opening routes, pricing tickets, and surviving the economic shocks that shaped real aviation history.

The game spans eight distinct aircraft eras, featuring **63 real aircraft** (Wright Flyer through to a Mach 5 Hermeus Halcyon), **52 world airports**, and historically accurate events that hit your bottom line exactly when they should.

---

## Features

- **63 aircraft** across eight eras, from the 1903 Wright Flyer to 2050 hydrogen flying wings
- **52 world airports** with an interactive equirectangular world map
- **Route management** — open, price, and staff any city pair
- **Fleet management** — buy, sell, assign, and configure cabin layouts per aircraft
- **Research tree** — unlock Premium Economy, Business Class, First Class, and Supersonic First
- **Historical events** — WWII, oil crises, deregulation, 9/11, COVID, and more trigger automatically in the correct year
- **Finance panel** — quarterly P&L, net worth chart, full transaction history
- **Save / load** — persist your airline across sessions

---

## Requirements

- Python 3.8+
- `tkinter` (standard library — requires Tcl/Tk to be installed)

### Install tkinter if missing

| Platform | Command |
|----------|---------|
| Ubuntu / Debian | `sudo apt install python3-tk` |
| Fedora / RHEL | `sudo dnf install python3-tkinter` |
| Arch Linux | `sudo pacman -S tk` |
| macOS (Homebrew) | `brew install python-tk` |

---

## Running the Game

```bash
python3 main.py
```

Or use the launcher script (handles multiple Python versions):

```bash
chmod +x run.sh && ./run.sh
```

---

## How to Play

### 1. Start a New Game
Choose your airline name, hub airport, starting year (1903–2040), and difficulty.

### 2. Fleet Tab
- Browse the aircraft market — only aircraft available in your current year are shown
- Purchase aircraft and assign them to routes
- Configure cabin layouts (Economy → Premium Economy → Business → First → Supersonic First)
- Sell ageing aircraft to fund upgrades

### 3. Routes Tab / World Map
- Open routes between any two of the 52 airports
- Click cities directly on the interactive map
- Set ticket prices — lower fares attract more passengers; premium cabins earn multiples
- Each active route requires at least one assigned aircraft

### 4. Advance Time
Click **Next Quarter** to advance 3 months:
- Revenue = passengers × ticket price × load-factor
- Costs = per-aircraft operating costs + overhead
- Historical events fire automatically, buffing or penalising your airline

### 5. Research Tab
Invest in R&D to unlock new cabin classes and gain competitive advantages.

---

## Aircraft Eras

| Era | Years | Highlight Aircraft |
|-----|-------|--------------------|
| Pioneer | 1903–1929 | Wright Flyer, Ford Trimotor |
| Golden Age | 1930–1945 | Boeing 314 Clipper |
| Piston Era | 1945–1957 | Lockheed Constellation, DC-7 |
| Jet Dawn | 1952–1969 | de Havilland Comet, Boeing 707, 727 |
| Wide Body | 1969–1982 | Boeing 747, Concorde, DC-10 |
| Modern | 1982–1999 | A320, 757/767, 747-400, 777 |
| 2000s | 2000–2019 | A380, 787 Dreamliner, A350 |
| Future | 2024–2050 | Boom Overture, ZEROe, Hermeus Halcyon (Mach 5), Starship Airliner |

---

## Project Structure

```
airlinesim/
├── main.py          # Application entry point, main menu, game loop
├── engine.py        # Game state, simulation logic, research projects
├── data.py          # Aircraft database (63 aircraft) and 52-city airport database
├── panels.py        # Fleet, Routes, Finance, Events, and Research UI panels
├── map_widget.py    # Interactive world map canvas widget
├── ui_theme.py      # Colour palette, fonts, and shared UI helpers
└── run.sh           # Cross-platform Python launcher script
```

---

## Built With

- **Python 3** — game logic and data
- **Tkinter** — GUI framework
- **No external dependencies** — runs out of the box on any Python 3.8+ installation with tkinter
