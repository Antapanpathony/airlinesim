╔══════════════════════════════════════════════════════════════════╗
║              AIRLINE EMPIRE  ·  1900 – 2050                      ║
║         Build your airline from biplane to hypersonic            ╗
╚══════════════════════════════════════════════════════════════════╝

REQUIREMENTS
  • Python 3.8+  with  tkinter  (standard library, needs Tcl/Tk)

INSTALL TKINTER (if not already present)
  Ubuntu / Debian:   sudo apt install python3-tk
  Fedora / RHEL:     sudo dnf install python3-tkinter
  Arch Linux:        sudo pacman -S tk
  macOS (Homebrew):  brew install python-tk

RUN THE GAME
  python3 main.py
  — or —
  chmod +x run.sh && ./run.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO PLAY

1. NEW GAME — choose your airline name, hub airport,
   starting year (1903–2040) and difficulty.

   Starting cash scales with the era and difficulty so that every
   start feels appropriately funded:

     Era example      Easy         Normal       Hard         Tycoon
     ──────────────   ──────────   ──────────   ──────────   ──────────
     1903 (Benoist)   $250 K       $100 K       $40 K        $15 K
     1950 (DC-6)      $35 M        $14 M        $5.6 M       $2.1 M
     1968 (B707)      $225 M       $90 M        $36 M        $13.5 M
     2000 (737NG)     $2.75 B      $1.1 B       $440 M       $165 M

   A starter aircraft suited to the era is gifted at no cost.

2. FLEET TAB
   • Browse the aircraft market (63 real aircraft, 1903–2050)
   • Purchase aircraft available in your current year
   • Assign aircraft to routes to start earning revenue
   • Sell older jets to raise upgrade capital
   • Aircraft condition degrades slowly over time (1–2 years to
     show wear; floor is 30%) — affects resale value

3. ROUTES TAB  (or click cities on the MAP)
   • Open routes between any two of 52 world airports
   • Set ticket prices — lower prices attract more passengers
   • Each active route needs at least one assigned aircraft
   • Demand depends on city populations, distance, and your
     airline's reputation

4. GAME SPEED  (top-right controls)
   The game runs in real time. Use the speed buttons to control
   how fast game days pass:

     ⏸  Paused
     1×  1 game-day ≈ 4 real seconds   (default)
     2×  1 game-day ≈ 1 real second
     4×  Fast-forward
     8×  Maximum speed

   Aircraft fly continuously — revenues and all costs (operating,
   overhead, airport fees) accrue in real time at every speed.

5. COSTS
   Each flight leg incurs:
   • Aircraft operating cost  — daily rate from monthly lease cost
   • Airport fees             — departure + landing charge per pax,
                                scaled by airport hub tier
                                (mega-hub > major > regional)
   • Overhead                 — admin/staff, scaled by fleet size
                                and era

6. FINANCE TAB — track profit/loss, net worth, monthly history
7. NEWS TAB    — full event log + aviation timeline

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AIRCRAFT ERAS

  Pioneer     1903–1929   Wright Flyer → Ford Trimotor
  Golden Age  1930–1945   Boeing 247 → Boeing 314 Clipper
  Piston Era  1945–1957   Constellation → Douglas DC-7
  Jet Dawn    1952–1969   Comet → Boeing 727 / DC-9
  Wide Body   1969–1982   747 · Concorde · DC-10 · TriStar
  Modern      1982–1999   757 / 767 · A320 · 747-400 · 777
  2000s       2000–2019   A380 · 787 · A350 · 737 MAX
  Future      2024–2050   777X · Boom Overture · ZEROe ·
                          Boeing NMA · Hermeus Halcyon (Mach 5) ·
                          Hydrogen BWB · Flying Wing 800-seat ·
                          SpaceX Starship Airliner (suborbital)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HISTORICAL EVENTS

  Major world events trigger automatically in the correct year,
  shifting passenger demand and your cash balance:

    1914  WWI — routes severely restricted
    1929  Wall Street Crash — passenger numbers plummet
    1945  WWII ends — pent-up travel demand explodes
    1952  Jet age begins (de Havilland Comet)
    1973  Oil Crisis — fuel costs triple
    1978  US Deregulation — new competition surges
    2001  9/11 — security costs soar
    2020  COVID-19 — global aviation enters freefall
    … and many more through 2050

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAP CONTROLS

  Left-click + drag    Pan the map
  Scroll wheel         Zoom in / out
  Click a city dot     Auto-fill route origin / destination
  Hover a city         Show city name label

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAVE / LOAD

  Click  Save  in the top bar at any time.
  Click  Load Game  from the main menu to resume.
  Save file: airline_empire/save.json
