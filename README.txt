╔══════════════════════════════════════════════════════════════════╗
║              AIRLINE EMPIRE  ·  1900 – 2050                      ║
║         Build your airline from biplane to hypersonic            ║
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

2. FLEET TAB
   • Browse the aircraft market (63 real aircraft, 1903–2050)
   • Purchase aircraft available in your starting year
   • Assign aircraft to routes; sell old jets for upgrade cash

3. ROUTES TAB  (or click cities on the MAP)
   • Open routes between any two of 52 world airports
   • Set ticket prices — lower prices attract more passengers
   • Each active route needs at least one assigned aircraft

4. NEXT QUARTER button
   • Advances time by 3 months
   • Revenue = passengers × ticket price × load-factor bonus
   • Costs  = aircraft operating costs + overhead
   • Historical events (WWII, oil crises, COVID, etc.) trigger
     automatically in the correct year, affecting your business

5. FINANCE TAB — track profit/loss, net worth, financial history
6. NEWS TAB    — full event log + aviation timeline

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
MAP CONTROLS

  Left-click + drag    Pan the map
  Scroll wheel         Zoom in / out
  Click a city dot     Auto-fill route origin / destination
  Hover a city         Show city name label

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAVE / LOAD

  Click  💾 Save  in the top bar at any time.
  Click  📂 Load Game  from the main menu to resume.
  Save file: airline_empire/save.json
