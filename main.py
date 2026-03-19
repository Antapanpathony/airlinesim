#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║          AIRLINE EMPIRE  ·  1900 – 2050              ║
║   Build your airline from biplane to hypersonic      ║
╚══════════════════════════════════════════════════════╝
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
import random
import time

# Ensure local modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from ui_theme import *
from data import CITIES, CITY_DICT, get_aircraft
from ui_theme import money_str, pax_str
from engine import GameState, GameEngine, ActiveFlight, FinancialRecord, OwnedAircraft, Route, new_game
from map_widget import WorldMap
from panels import FleetPanel, RoutesPanel, FinancePanel, EventsPanel

SAVE_FILE = os.path.join(os.path.dirname(__file__), 'save.json')
APP_TITLE = 'Airline Empire  ·  1900 – 2050'
VERSION   = '1.0'

# ─────────────────────────────────────────────────────────────────────────────
# MAIN MENU SCREEN
# ─────────────────────────────────────────────────────────────────────────────
class MainMenuScreen(tk.Frame):
    def __init__(self, parent, on_new_game, on_load_game, on_quit, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.on_new_game  = on_new_game
        self.on_load_game = on_load_game
        self.on_quit      = on_quit
        self._build()

    def _build(self):
        # Background canvas with animated sky
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._canvas.bind('<Configure>', self._draw_bg)
        self.after(50, self._draw_bg)

        # Center container
        center = tk.Frame(self, bg='', bd=0)
        center.place(relx=0.5, rely=0.5, anchor='center')

        # Logo / title
        logo_frame = tk.Frame(center, bg=BG2, padx=40, pady=30,
                               relief='flat', bd=0)
        logo_frame.pack(pady=10)

        # Decorative banner
        tk.Label(logo_frame, text='✈  ✈  ✈',
                 fg=GOLD, bg=BG2, font=('Helvetica', 18)).pack()

        tk.Label(logo_frame, text='AIRLINE EMPIRE',
                 fg=WHITE, bg=BG2,
                 font=('Helvetica', 38, 'bold')).pack(pady=(6, 0))

        tk.Label(logo_frame, text='1900  ·  TO  ·  2050',
                 fg=ACCENT2, bg=BG2,
                 font=('Helvetica', 14, 'bold')).pack(pady=2)

        tk.Label(logo_frame,
                 text='Build your airline from a pioneer biplane\nto hypersonic jets and hydrogen giants.',
                 fg=TEXT2, bg=BG2,
                 font=('Helvetica', 11), justify='center').pack(pady=(12, 0))

        separator(logo_frame).pack(fill='x', pady=14)

        btns = tk.Frame(logo_frame, bg=BG2)
        btns.pack()
        self._make_btn(btns, '✈   NEW GAME', self.on_new_game, GOLD, BG, 24).pack(
            fill='x', pady=4)
        self._make_btn(btns, '📂   LOAD GAME', self.on_load_game, ACCENT, WHITE, 14).pack(
            fill='x', pady=4)
        self._make_btn(btns, '✖   QUIT', self.on_quit, '#2a1a1a', RED, 13).pack(
            fill='x', pady=4)

        tk.Label(logo_frame, text=f'v{VERSION}  —  All aircraft historically verified',
                 fg=MUTED, bg=BG2, font=('Helvetica', 8)).pack(pady=(14, 0))

    def _make_btn(self, parent, text, cmd, bg, fg, fs):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         font=('Helvetica', fs, 'bold'), relief='flat', bd=0,
                         cursor='hand2', padx=30, pady=10,
                         activebackground=lerp_color(bg, WHITE, 0.2),
                         activeforeground=fg)

    def _draw_bg(self, event=None):
        c = self._canvas
        w = c.winfo_width() or 1400
        h = c.winfo_height() or 900
        c.delete('all')
        # Gradient sky
        steps = 30
        for i in range(steps):
            t = i / steps
            col = lerp_color('#040c1a', '#0d2a4a', t)
            y1 = int(i * h / steps)
            y2 = int((i+1) * h / steps)
            c.create_rectangle(0, y1, w, y2, fill=col, outline='')

        # Stars
        random.seed(42)
        for _ in range(200):
            sx = random.randint(0, w)
            sy = random.randint(0, int(h * 0.7))
            br = random.random()
            col = lerp_color('#1a3a60', WHITE, br * 0.7)
            r = 1 if br < 0.7 else 2
            c.create_oval(sx-r, sy-r, sx+r, sy+r, fill=col, outline='')

        # Horizon glow
        for i in range(20):
            t = i / 20
            alpha = (1 - t) * 0.6
            col = lerp_color('#0a1e3a', '#1a4a7a', t)
            yh = int(h * 0.55 + i * 3)
            c.create_line(0, yh, w, yh, fill=col, width=3)

        # Silhouette of airplane
        self._draw_plane(c, w*0.15, h*0.35, scale=1.4)
        self._draw_plane(c, w*0.78, h*0.28, scale=0.8)
        self._draw_plane(c, w*0.52, h*0.18, scale=0.5)

    def _draw_plane(self, c, cx, cy, scale=1.0):
        s = scale
        col = '#1a3550'
        # Fuselage
        c.create_oval(cx-40*s, cy-6*s, cx+40*s, cy+6*s, fill=col, outline='')
        # Wings
        c.create_polygon(
            cx-5*s, cy,  cx+10*s, cy-3*s,
            cx+5*s, cy-20*s,  cx-20*s, cy,
            fill=col, outline='')
        c.create_polygon(
            cx-5*s, cy,  cx+10*s, cy+3*s,
            cx+5*s, cy+20*s,  cx-20*s, cy,
            fill=col, outline='')
        # Tail
        c.create_polygon(
            cx+30*s, cy,  cx+50*s, cy-12*s,
            cx+50*s, cy,
            fill=col, outline='')


# ─────────────────────────────────────────────────────────────────────────────
# SETUP SCREEN
# ─────────────────────────────────────────────────────────────────────────────
class SetupScreen(tk.Frame):
    def __init__(self, parent, on_start, on_back, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.on_start = on_start
        self.on_back  = on_back
        self._build()

    def _build(self):
        tk.Button(self, text='← Back', command=self.on_back,
                  bg=BG2, fg=TEXT2, font=('Helvetica',10), relief='flat',
                  cursor='hand2', padx=10, pady=5).pack(anchor='nw', padx=10, pady=10)

        center = tk.Frame(self, bg=BG2, padx=40, pady=30)
        center.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(center, text='FOUND YOUR AIRLINE', fg=GOLD, bg=BG2,
                 font=('Helvetica', 22, 'bold')).pack(pady=(0, 20))

        fields = tk.Frame(center, bg=BG2)
        fields.pack()

        def row(lbl, widget_fn, row_i):
            tk.Label(fields, text=lbl, fg=TEXT2, bg=BG2,
                     font=('Helvetica', 11), width=18, anchor='e').grid(
                     row=row_i, column=0, padx=(0,10), pady=8, sticky='e')
            w = widget_fn(fields)
            w.grid(row=row_i, column=1, sticky='ew', pady=8)
            return w

        # Airline name
        self._name_var = tk.StringVar(value='Eagle Air')
        row('Airline Name:', lambda p: tk.Entry(p, textvariable=self._name_var,
            bg=BG3, fg=TEXT, font=('Helvetica',12), relief='flat',
            insertbackground=TEXT, width=22), 0)

        # Start year
        self._year_var = tk.IntVar(value=1960)
        yr_frame = lambda p: self._make_year_frame(p)
        row('Starting Year:', yr_frame, 1)

        # Hub city
        self._hub_var = tk.StringVar(value='JFK')
        city_values = [f'{c.code} — {c.name}, {c.country}' for c in CITIES]
        hub_cb = lambda p: ttk.Combobox(p, textvariable=self._hub_var,
                                         values=[c.code for c in CITIES],
                                         state='readonly', width=20,
                                         font=('Helvetica',11))
        row('Hub Airport:', hub_cb, 2)

        # Difficulty
        self._diff_var = tk.StringVar(value='normal')
        diff_frame = lambda p: self._make_diff_frame(p)
        row('Difficulty:', diff_frame, 3)

        separator(center).pack(fill='x', pady=16)

        # Start button
        tk.Button(center, text='✈   LAUNCH AIRLINE',
                  command=self._on_start_click,
                  bg=GOLD, fg=BG, font=('Helvetica',15,'bold'),
                  relief='flat', cursor='hand2', padx=30, pady=12,
                  activebackground='#f0c060', activeforeground=BG).pack(fill='x')

    def _make_year_frame(self, parent):
        f = tk.Frame(parent, bg=BG2)
        self._year_scale = tk.Scale(f, variable=self._year_var,
                                     from_=1903, to=2040, orient='horizontal',
                                     length=220, bg=BG2, fg=TEXT, troughcolor=BG3,
                                     highlightthickness=0, font=('Helvetica',9),
                                     activebackground=ACCENT, sliderrelief='flat',
                                     command=self._update_year_label)
        self._year_scale.pack(side='left')
        self._year_lbl = tk.Label(f, text='1960', fg=GOLD, bg=BG2,
                                   font=('Helvetica',13,'bold'), width=5)
        self._year_lbl.pack(side='left', padx=6)
        return f

    def _update_year_label(self, val):
        self._year_lbl.config(text=str(int(float(val))))

    def _make_diff_frame(self, parent):
        f = tk.Frame(parent, bg=BG2)
        diffs = [
            ('easy',   'Easy',   GREEN,  '$25M starting budget'),
            ('normal', 'Normal', ACCENT2,'$10M starting budget'),
            ('hard',   'Hard',   ORANGE, '$5M starting budget'),
            ('tycoon', 'Tycoon', RED,    '$2M — no mercy'),
        ]
        for val, label, color, tip in diffs:
            btn = tk.Radiobutton(f, text=label, variable=self._diff_var, value=val,
                                  bg=BG2, fg=color, activebackground=BG2,
                                  selectcolor=BG3, font=('Helvetica',10,'bold'),
                                  indicatoron=True, cursor='hand2')
            btn.pack(side='left', padx=6)
        return f

    def _on_start_click(self):
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning('Missing Name', 'Please enter an airline name.', parent=self)
            return
        self.on_start(name, self._hub_var.get(), self._year_var.get(), self._diff_var.get())


# ─────────────────────────────────────────────────────────────────────────────
# GAME SCREEN
# ─────────────────────────────────────────────────────────────────────────────
# Game-speed levels: game-hours per real-second
#  0=paused, 1x=6h/s (1 day≈4s), 2x=24h/s (1 day=1s),
#  4x=96h/s (fast-forward), 8x=384h/s (max)
_SPEED_GH = [0, 6, 24, 96, 384]
_SPEED_LABELS = ['⏸', '1×', '2×', '4×', '8×']


class GameScreen(tk.Frame):
    def __init__(self, parent, state: GameState, engine: GameEngine, on_menu, **kw):
        super().__init__(parent, bg=BG, **kw)
        self.state  = state
        self.engine = engine
        self.on_menu = on_menu
        self._active_tab = 'map'
        self._speed_idx = 1          # default 1×
        self._last_tick = time.time()
        self._loop_id   = None
        self._popup_open = False
        self._map_tick  = 0
        self._build()
        self.refresh_all()
        self._start_loop()

    def _build(self):
        # ── Top bar ──────────────────────────────────────────────────────────
        self._topbar = tk.Frame(self, bg=BG2, height=54)
        self._topbar.pack(fill='x', side='top')
        self._topbar.pack_propagate(False)
        self._build_topbar()

        # ── Bottom bar ───────────────────────────────────────────────────────
        self._botbar = tk.Frame(self, bg=BG, height=40)
        self._botbar.pack(fill='x', side='bottom')
        self._botbar.pack_propagate(False)
        self._build_botbar()

        # ── Main area ────────────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill='both', expand=True, side='top')

        # Left sidebar
        self._sidebar = tk.Frame(main, bg=BG2, width=120)
        self._sidebar.pack(side='left', fill='y')
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self._content = tk.Frame(main, bg=BG2)
        self._content.pack(side='left', fill='both', expand=True)

        self._panels = {}
        self._build_panels()
        self._show_tab('map')

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _build_topbar(self):
        tb = self._topbar

        # Airline name / logo
        left = tk.Frame(tb, bg=BG2)
        left.pack(side='left', padx=14, pady=6)

        self._airline_lbl = tk.Label(left, text='', fg=WHITE, bg=BG2,
                                      font=('Helvetica', 16, 'bold'))
        self._airline_lbl.pack(anchor='w')
        self._hub_lbl = tk.Label(left, text='', fg=TEXT2, bg=BG2,
                                  font=('Helvetica', 9))
        self._hub_lbl.pack(anchor='w')

        # Stats
        stats_frame = tk.Frame(tb, bg=BG2)
        stats_frame.pack(side='left', fill='y', padx=20)

        self._stat_lbls = {}
        for col, (label, key, fg) in enumerate([
            ('YEAR',  'year',  ACCENT2),
            ('CASH',  'cash',  GOLD),
            ('FLEET', 'fleet', TEXT),
            ('ROUTES','routes',TEXT),
            ('REP',   'rep',   GREEN),
            ('PAX',   'pax',   TEXT2),
        ]):
            cell = tk.Frame(stats_frame, bg=BG2)
            cell.grid(row=0, column=col, padx=14)
            tk.Label(cell, text=label, fg=MUTED, bg=BG2,
                     font=('Helvetica',7,'bold')).pack()
            lbl = tk.Label(cell, text='—', fg=fg, bg=BG2,
                           font=('Helvetica',12,'bold'))
            lbl.pack()
            self._stat_lbls[key] = lbl

        # Right: buttons
        right = tk.Frame(tb, bg=BG2)
        right.pack(side='right', padx=10, pady=8)
        tk.Button(right, text='💾 Save', command=self._save,
                  bg=BG3, fg=TEXT2, font=('Helvetica',9), relief='flat',
                  cursor='hand2', padx=8, pady=4).pack(side='left', padx=2)
        tk.Button(right, text='🏠 Menu', command=self.on_menu,
                  bg=BG3, fg=TEXT2, font=('Helvetica',9), relief='flat',
                  cursor='hand2', padx=8, pady=4).pack(side='left', padx=2)

    def _update_topbar(self):
        s = self.state
        hub_city = CITY_DICT.get(s.hub_code)
        hub_name = f'{hub_city.name}, {hub_city.country}' if hub_city else s.hub_code
        self._airline_lbl.config(text=f'✈  {s.airline_name}')
        self._hub_lbl.config(text=f'Hub: {s.hub_code} · {hub_name}')

        self._stat_lbls['year'].config(text=s.date_str())
        self._stat_lbls['cash'].config(
            text=money_str(s.cash),
            fg=GOLD if s.cash >= 0 else RED)
        self._stat_lbls['fleet'].config(text=str(len(s.fleet)))
        self._stat_lbls['routes'].config(text=str(len(s.routes)))
        self._stat_lbls['rep'].config(
            text=f'{s.reputation:.0f}%',
            fg=GREEN if s.reputation >= 60 else (ORANGE if s.reputation >= 30 else RED))
        self._stat_lbls['pax'].config(text=pax_str(s.total_pax))

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = self._sidebar
        tk.Label(sb, text='', bg=BG2, height=1).pack()

        nav_items = [
            ('map',     '🗺',  'Map'),
            ('fleet',   '✈',   'Fleet'),
            ('routes',  '↔',   'Routes'),
            ('finance', '💰',  'Finance'),
            ('events',  '📰',  'News'),
        ]
        self._nav_btns = {}
        for tab_id, icon, label in nav_items:
            btn = tk.Button(sb,
                text=f'{icon}\n{label}',
                command=lambda t=tab_id: self._show_tab(t),
                bg=BG2, fg=TEXT2,
                font=('Helvetica', 9, 'bold'),
                relief='flat', bd=0, cursor='hand2',
                padx=10, pady=10, width=9,
                activebackground=HOVER, activeforeground=WHITE)
            btn.pack(fill='x', pady=1, padx=4)
            self._nav_btns[tab_id] = btn

    def _show_tab(self, tab_id: str):
        self._active_tab = tab_id
        for tid, btn in self._nav_btns.items():
            if tid == tab_id:
                btn.config(bg=SEL, fg=GOLD)
            else:
                btn.config(bg=BG2, fg=TEXT2)

        for tid, panel in self._panels.items():
            if tid == tab_id:
                panel.pack(fill='both', expand=True)
            else:
                panel.pack_forget()

        self._refresh_panel(tab_id)

    def _refresh_panel(self, tab_id):
        panel = self._panels.get(tab_id)
        if panel and hasattr(panel, 'refresh'):
            panel.refresh()

    # ── Panels ────────────────────────────────────────────────────────────────
    def _build_panels(self):
        cont = self._content

        # Map panel
        map_outer = tk.Frame(cont, bg=BG2)
        self._map_widget = WorldMap(map_outer, game_state=self.state,
                                     on_city_click=self._on_map_city_click)
        self._map_widget.pack(fill='both', expand=True)
        self._panels['map'] = map_outer

        # Fleet panel
        fleet_panel = FleetPanel(cont, self.state, self.engine,
                                  refresh_cb=self.refresh_all)
        self._panels['fleet'] = fleet_panel

        # Routes panel
        routes_panel = RoutesPanel(cont, self.state, self.engine,
                                    on_map_refresh=self._refresh_map,
                                    refresh_cb=self.refresh_all)
        self._panels['routes'] = routes_panel

        # Finance panel
        finance_panel = FinancePanel(cont, self.state)
        self._panels['finance'] = finance_panel

        # Events panel
        events_panel = EventsPanel(cont, self.state)
        self._panels['events'] = events_panel

    def _on_map_city_click(self, city):
        """When user clicks a city on the map, fill route fields."""
        # Switch to routes tab and set city
        self._show_tab('routes')
        routes_panel = self._panels.get('routes')
        if routes_panel and hasattr(routes_panel, 'set_city'):
            routes_panel.set_city(city.code)

    def _refresh_map(self):
        self._map_widget.redraw()

    # ── Bottom bar ────────────────────────────────────────────────────────────
    def _build_botbar(self):
        bb = self._botbar

        self._status_lbl = tk.Label(bb, text='', fg=TEXT2, bg=BG,
                                     font=('Helvetica', 9), anchor='w')
        self._status_lbl.pack(side='left', padx=12, fill='y')

        # Quick stats
        self._qstat_lbl = tk.Label(bb, text='', fg=MUTED, bg=BG,
                                    font=('Helvetica', 9), anchor='e')
        self._qstat_lbl.pack(side='right', padx=14)

        # Speed controls
        speed_frame = tk.Frame(bb, bg=BG)
        speed_frame.pack(side='right', padx=4, pady=5)
        tk.Label(speed_frame, text='SPEED:', fg=MUTED, bg=BG,
                 font=('Helvetica', 8)).pack(side='left', padx=(0, 3))
        self._speed_btns = []
        for i, lbl in enumerate(_SPEED_LABELS):
            btn = tk.Button(speed_frame, text=lbl,
                            command=lambda idx=i: self._set_speed(idx),
                            bg=BG3, fg=TEXT2,
                            font=('Helvetica', 10, 'bold'),
                            relief='flat', bd=0, cursor='hand2',
                            padx=9, pady=2,
                            activebackground=HOVER, activeforeground=WHITE)
            btn.pack(side='left', padx=1)
            self._speed_btns.append(btn)
        self._update_speed_btns()

    def _set_status(self, msg: str, color=TEXT2):
        self._status_lbl.config(text=msg, fg=color)

    # ── Speed controls ────────────────────────────────────────────────────────
    def _set_speed(self, idx: int):
        self._speed_idx = idx
        self._update_speed_btns()

    def _update_speed_btns(self):
        for i, btn in enumerate(self._speed_btns):
            if i == self._speed_idx:
                btn.config(bg=ACCENT, fg=WHITE)
            else:
                btn.config(bg=BG3, fg=TEXT2)

    # ── Real-time game loop ───────────────────────────────────────────────────
    def _start_loop(self):
        self._last_tick = time.time()
        self._game_loop()

    def _game_loop(self):
        if not self.winfo_exists():
            return

        now = time.time()
        dt_real = min(now - self._last_tick, 0.5)  # cap at 0.5s to avoid huge jumps
        self._last_tick = now

        gh_per_sec = _SPEED_GH[self._speed_idx]
        delta_hours = dt_real * gh_per_sec

        if delta_hours > 0:
            result = self.engine.tick(delta_hours)

            # Events popup (pause while showing)
            if result['events'] and not self._popup_open:
                self._show_events_popup(result['events'])

            # Bankruptcy check
            if self.state.cash < -50 and not self._popup_open:
                self._speed_idx = 0
                self._update_speed_btns()
                self._popup_open = True
                messagebox.showerror('BANKRUPTCY',
                    f'{self.state.airline_name} has gone bankrupt!\n'
                    f'Cash: {money_str(self.state.cash)}\n\n'
                    'Game over. Return to menu.',
                    parent=self)
                self._popup_open = False
                self.on_menu()
                return

            # Victory
            if self.state.year > 2050 and not self._popup_open:
                self._speed_idx = 0
                self._update_speed_btns()
                self._popup_open = True
                messagebox.showinfo('CONGRATULATIONS!',
                    f'You have guided {self.state.airline_name} through aviation history!\n\n'
                    f'Total passengers carried: {pax_str(self.state.total_pax)}\n'
                    f'Net worth: {money_str(self.state.net_worth)}\n\n'
                    f'🏆 Achievement: Master of the Skies',
                    parent=self)
                self._popup_open = False

            # Update top bar every tick (date, cash, stats)
            self._update_topbar()

            # Refresh map every 4 ticks ≈ 200ms (for moving flight dots)
            self._map_tick += 1
            if self._map_tick >= 4:
                self._map_tick = 0
                self._refresh_map()

            # Refresh the active panel every ~2s so data stays current.
            # 2s gap is long enough not to disrupt treeview clicks/selections.
            self._panel_tick = getattr(self, '_panel_tick', 0) + 1
            if self._panel_tick >= 40:
                self._panel_tick = 0
                self._refresh_panel(self._active_tab)

            # Status bar: live flight/cash info
            n_flights = len(self.state.active_flights)
            cash_col = GREEN if self.state.cash >= 0 else RED
            self._set_status(
                f'Flights airborne: {n_flights}  |  '
                f'Pax carried: {pax_str(self.state.total_pax)}  |  '
                f'Net worth: {money_str(self.state.net_worth)}',
                TEXT2,
            )

        self._loop_id = self.after(50, self._game_loop)

    def _show_events_popup(self, events):
        self._popup_open = True
        prev_speed = self._speed_idx
        self._speed_idx = 0
        self._update_speed_btns()

        popup = tk.Toplevel(self)
        popup.title('Breaking News')
        popup.configure(bg=BG2)
        popup.geometry('520x300')
        popup.transient(self)
        popup.grab_set()

        tk.Label(popup, text='📰  BREAKING NEWS', fg=GOLD, bg=BG2,
                 font=('Helvetica', 16, 'bold')).pack(pady=(20, 10))
        for ev in events:
            tk.Label(popup, text=ev, fg=TEXT, bg=BG2,
                     font=('Helvetica', 11), wraplength=460,
                     justify='center').pack(pady=4)

        def on_continue():
            self._speed_idx = prev_speed
            self._update_speed_btns()
            self._popup_open = False
            popup.destroy()

        tk.Button(popup, text='Continue', command=on_continue,
                  bg=ACCENT, fg=WHITE, font=('Helvetica', 11, 'bold'),
                  relief='flat', padx=20, pady=6, cursor='hand2').pack(pady=16)
        self.wait_window(popup)

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh_all(self):
        self._update_topbar()
        self._refresh_map()
        if self._active_tab != 'map':
            self._refresh_panel(self._active_tab)

        active_routes = sum(1 for r in self.state.routes if r.aircraft_ids)
        self._qstat_lbl.config(
            text=f'Active routes: {active_routes}/{len(self.state.routes)}  |  '
                 f'Fleet: {len(self.state.fleet)} aircraft  |  '
                 f'In-flight: {len(self.state.active_flights)}')

    def destroy(self):
        if self._loop_id:
            self.after_cancel(self._loop_id)
        super().destroy()

    # ── Save/Load ─────────────────────────────────────────────────────────────
    def _save(self):
        try:
            import dataclasses
            data = dataclasses.asdict(self.state)
            with open(SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            self._set_status('Game saved.', GREEN)
        except Exception as e:
            messagebox.showerror('Save Error', str(e), parent=self)


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION ROOT
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry('1400x860')
        self.minsize(1100, 700)
        self.configure(bg=BG)
        apply_theme(self)

        try:
            self.iconbitmap('')  # clear default icon
        except Exception:
            pass

        self._current_screen = None
        self._state  = None
        self._engine = None

        self._show_menu()

    def _clear(self):
        if self._current_screen:
            self._current_screen.destroy()
            self._current_screen = None

    def _show_menu(self):
        self._clear()
        scr = MainMenuScreen(self,
                              on_new_game=self._show_setup,
                              on_load_game=self._load_game,
                              on_quit=self.quit)
        scr.pack(fill='both', expand=True)
        self._current_screen = scr

    def _show_setup(self):
        self._clear()
        scr = SetupScreen(self, on_start=self._start_game, on_back=self._show_menu)
        scr.pack(fill='both', expand=True)
        self._current_screen = scr

    def _start_game(self, name: str, hub: str, year: int, difficulty: str):
        self._state  = new_game(name, hub, year, difficulty)
        self._engine = GameEngine(self._state)
        self._show_game()

    def _show_game(self):
        self._clear()
        scr = GameScreen(self, self._state, self._engine, on_menu=self._show_menu)
        scr.pack(fill='both', expand=True)
        self._current_screen = scr

    def _load_game(self):
        if not os.path.exists(SAVE_FILE):
            messagebox.showinfo('No Save', 'No saved game found.', parent=self)
            return
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)

            # Migrate from old quarter-based saves
            data.pop('quarter', None)
            data.setdefault('month', 1)
            data.setdefault('day', 1)
            data.setdefault('game_day', 0.0)
            data.setdefault('_period_revenue', 0.0)
            data.setdefault('_period_costs', 0.0)

            # Rebuild nested dataclasses
            fleet = [OwnedAircraft(**o) for o in data.get('fleet', [])]
            routes = [Route(**r) for r in data.get('routes', [])]

            raw_flights = data.get('active_flights', [])
            active_flights = [ActiveFlight(**f) for f in raw_flights]

            history = []
            for h in data.get('finance_history', []):
                if 'quarter' in h:
                    h['month'] = h.pop('quarter')
                history.append(FinancialRecord(**h))

            data['fleet'] = fleet
            data['routes'] = routes
            data['active_flights'] = active_flights
            data['finance_history'] = history

            self._state = GameState(**data)
            self._engine = GameEngine(self._state)
            self._show_game()
        except Exception as e:
            messagebox.showerror('Load Error',
                f'Could not load save file:\n{e}', parent=self)


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
