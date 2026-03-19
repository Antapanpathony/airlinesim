"""Game panels: Fleet, Routes, Finance, Events"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
from ui_theme import *
from data import AIRCRAFT_DB, CITY_DICT, CITIES, get_aircraft, available_aircraft
from engine import GameEngine

# ─────────────────────────────────────────────────────────────────────────────
# FLEET PANEL
# ─────────────────────────────────────────────────────────────────────────────
class FleetPanel(tk.Frame):
    def __init__(self, parent, state, engine: GameEngine, refresh_cb=None, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self.engine = engine
        self.refresh_cb = refresh_cb
        self._build()

    def _build(self):
        # Left: owned aircraft
        left = tk.Frame(self, bg=BG2)
        left.pack(side='left', fill='both', expand=True, padx=(0, 2))

        tk.Label(left, text='YOUR FLEET', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(10, 4))

        cols = ('name','type','pax','range','condition','route','age')
        self._fleet_tree = ttk.Treeview(left, columns=cols, show='headings',
                                         selectmode='browse', style='Treeview')
        hdrs = [('name','Aircraft',180),('type','Class',75),
                ('pax','Seats',50),('range','Range',90),
                ('condition','Cond.',60),('route','Route',90),('age','Age',40)]
        for col, hdr, w in hdrs:
            self._fleet_tree.heading(col, text=hdr)
            self._fleet_tree.column(col, width=w, anchor='center')
        self._fleet_tree.column('name', anchor='w')

        sb = ttk.Scrollbar(left, orient='vertical', command=self._fleet_tree.yview)
        self._fleet_tree.configure(yscrollcommand=sb.set)
        self._fleet_tree.pack(side='left', fill='both', expand=True, padx=(8,0), pady=4)
        sb.pack(side='left', fill='y', pady=4)

        btn_row = tk.Frame(left, bg=BG2)
        btn_row.pack(fill='x', padx=8, pady=4)
        icon_btn(btn_row, '✈  Assign to Route', self._assign_route,
                 color=ACCENT, font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '⬛  Remove from Route', self._remove_route,
                 color='#1a3050', font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '💰  Sell Aircraft', self._sell_aircraft,
                 color='#5a1a1a', font=F_SMALL).pack(side='left', padx=2)

        # Detail card (packed first so it anchors to the far right)
        self._detail = tk.Frame(self, bg=BG3, width=220)
        self._detail.pack(side='right', fill='y', padx=(2,8), pady=8)
        self._detail.pack_propagate(False)
        self._detail_lbl = tk.Label(self._detail, text='Select an aircraft\nto view details',
                                     fg=TEXT2, bg=BG3, font=F_SMALL, justify='left',
                                     wraplength=200)
        self._detail_lbl.pack(padx=10, pady=10, anchor='nw')
        self._buy_btn = icon_btn(self._detail, '🛒  Purchase', self._buy_aircraft,
                                  color=GREEN, font=F_SMALL)
        self._buy_btn.pack(padx=10, pady=4, fill='x')
        self._buy_btn.config(state='disabled')

        # Right: marketplace (packed after detail, so it sits left of the detail card)
        right = tk.Frame(self, bg=BG2, width=420)
        right.pack(side='right', fill='both', padx=(2, 0))
        right.pack_propagate(False)

        tk.Label(right, text='AIRCRAFT MARKET', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(10, 2))

        # Filter row
        filt = tk.Frame(right, bg=BG2)
        filt.pack(fill='x', padx=8, pady=2)
        tk.Label(filt, text='Class:', fg=TEXT2, bg=BG2, font=F_SMALL).pack(side='left')
        self._cat_var = tk.StringVar(value='All')
        cats = ttk.Combobox(filt, textvariable=self._cat_var, width=12,
                             values=['All','pioneer','regional','narrow','wide','supersonic','future'],
                             state='readonly', font=F_SMALL)
        cats.pack(side='left', padx=4)
        cats.bind('<<ComboboxSelected>>', lambda e: self._populate_market())

        cols2 = ('name','year','pax','range','speed','cost')
        self._market_tree = ttk.Treeview(right, columns=cols2, show='headings',
                                          selectmode='browse', style='Treeview')
        hdrs2 = [('name','Aircraft',170),('year','Avail.',45),
                 ('pax','Seats',50),('range','Range',75),
                 ('speed','Speed',75),('cost','Cost',75)]
        for col, hdr, w in hdrs2:
            self._market_tree.heading(col, text=hdr)
            self._market_tree.column(col, width=w, anchor='center')
        self._market_tree.column('name', anchor='w')
        self._market_tree.bind('<<TreeviewSelect>>', self._on_market_select)

        sb2 = ttk.Scrollbar(right, orient='vertical', command=self._market_tree.yview)
        self._market_tree.configure(yscrollcommand=sb2.set)
        self._market_tree.pack(side='left', fill='both', expand=True, padx=(8,0), pady=4)
        sb2.pack(side='left', fill='y', pady=4)

        self._selected_ac = None
        self.refresh()

    def refresh(self):
        self._populate_fleet()
        self._populate_market()

    def _populate_fleet(self):
        sel = self._fleet_tree.selection()
        for item in self._fleet_tree.get_children():
            self._fleet_tree.delete(item)
        for owned in self.state.fleet:
            ac = get_aircraft(owned.ac_id)
            cat = ac.category if ac else '?'
            pax = ac.passengers if ac else '?'
            rng = f'{ac.range_km:,}km' if ac else '?'
            cond = f'{owned.condition*100:.0f}%'
            route = owned.assigned_route or '—'
            age = self.state.year - owned.year_acquired
            tag = 'good' if owned.condition > 0.7 else ('warn' if owned.condition > 0.4 else 'bad')
            self._fleet_tree.insert('', 'end',
                iid=str(owned.serial),
                values=(owned.name, cat, pax, rng, cond, route, age),
                tags=(tag,))
        self._fleet_tree.tag_configure('good', foreground=TEXT)
        self._fleet_tree.tag_configure('warn', foreground=ORANGE)
        self._fleet_tree.tag_configure('bad',  foreground=RED)
        for iid in sel:
            if self._fleet_tree.exists(iid):
                self._fleet_tree.selection_set(iid)

    def _populate_market(self):
        sel = self._market_tree.selection()
        for item in self._market_tree.get_children():
            self._market_tree.delete(item)
        cat_filter = self._cat_var.get()
        for ac in AIRCRAFT_DB:
            if cat_filter != 'All' and ac.category != cat_filter:
                continue
            avail = ac.year <= self.state.year
            tag = 'avail' if avail else 'future'
            yr_str = str(ac.year) if not avail else '✓'
            speed_str = f'M{ac.speed_kmh/1225:.1f}' if ac.speed_kmh > 1200 else f'{ac.speed_kmh}km/h'
            self._market_tree.insert('', 'end', iid=ac.id,
                values=(ac.name, yr_str, ac.passengers,
                        f'{ac.range_km:,}km' if ac.range_km > 0 else 'Orbital',
                        speed_str, money_str(ac.cost_m)),
                tags=(tag,))
        self._market_tree.tag_configure('avail',  foreground=TEXT)
        self._market_tree.tag_configure('future', foreground=MUTED)
        for iid in sel:
            if self._market_tree.exists(iid):
                self._market_tree.selection_set(iid)

    def _on_market_select(self, event):
        sel = self._market_tree.selection()
        if not sel:
            return
        ac_id = sel[0]
        ac = get_aircraft(ac_id)
        if not ac:
            return
        self._selected_ac = ac
        avail = ac.year <= self.state.year
        affordable = ac.cost_m <= self.state.cash
        fuel_icons = {'jet':'⛽','avgas':'🛢','hydrogen':'💧','electric':'⚡','saf':'🌱','methane':'🔥'}
        fuel_icon = fuel_icons.get(ac.fuel_type, '⛽')
        cat_icons = {'pioneer':'🪂','regional':'🛩','narrow':'✈','wide':'🛫',
                     'supersonic':'🚀','future':'🔮'}
        cat_icon = cat_icons.get(ac.category, '✈')
        speed_str = f'Mach {ac.speed_kmh/1225:.1f}' if ac.speed_kmh > 1200 else f'{ac.speed_kmh} km/h'
        range_str = 'Suborbital' if ac.range_km <= 0 else f'{ac.range_km:,} km'
        status = '✅ Available' if avail else f'🔒 Available {ac.year}'
        cost_color = GREEN if affordable else RED
        details = (
            f'{cat_icon} {ac.name}\n'
            f'{'─'*28}\n'
            f'🏭  {ac.manufacturer}\n'
            f'📅  {ac.year} · {status}\n\n'
            f'👥  {ac.passengers} passengers\n'
            f'📏  {range_str}\n'
            f'💨  {speed_str}\n'
            f'{fuel_icon}  {ac.fuel_type.title()} propulsion\n\n'
            f'💰  {money_str(ac.cost_m)}\n'
            f'🔧  {money_str(ac.monthly_cost_k/1000)}/month ops\n\n'
            f'📖  {ac.notes}'
        )
        self._detail_lbl.config(text=details, fg=TEXT if avail else MUTED)
        if avail and affordable:
            self._buy_btn.config(state='normal', bg=GREEN)
        else:
            self._buy_btn.config(state='disabled', bg=MUTED)

    def _buy_aircraft(self):
        if not self._selected_ac:
            return
        ok, msg = self.engine.buy_aircraft(self._selected_ac)
        if ok:
            messagebox.showinfo('Purchase', msg, parent=self)
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()
        else:
            messagebox.showerror('Cannot Purchase', msg, parent=self)

    def _get_selected_serial(self):
        sel = self._fleet_tree.selection()
        if not sel:
            messagebox.showwarning('Select Aircraft', 'Select an aircraft from your fleet.', parent=self)
            return None
        return int(sel[0])

    def _assign_route(self):
        serial = self._get_selected_serial()
        if serial is None:
            return
        if not self.state.routes:
            messagebox.showinfo('No Routes', 'Open some routes first in the Routes panel.', parent=self)
            return
        route_options = [f'{r.id} ({r.distance_km:.0f}km)' for r in self.state.routes]
        choice = simpledialog.askstring('Assign Route',
            f'Choose route:\n' + '\n'.join(f'  {i+1}. {r}' for i, r in enumerate(route_options)),
            parent=self)
        if not choice:
            return
        # Try to parse number or ID
        rid = None
        try:
            idx = int(choice.strip()) - 1
            if 0 <= idx < len(self.state.routes):
                rid = self.state.routes[idx].id
        except ValueError:
            rid = choice.strip().upper()
        if rid:
            ok, msg = self.engine.assign_aircraft(serial, rid)
            if ok:
                self.refresh()
                if self.refresh_cb:
                    self.refresh_cb()
            else:
                messagebox.showerror('Cannot Assign', msg, parent=self)

    def _remove_route(self):
        serial = self._get_selected_serial()
        if serial is None:
            return
        ok, msg = self.engine.unassign_aircraft(serial)
        if ok:
            self.refresh()
        else:
            messagebox.showwarning('Cannot Remove', msg, parent=self)

    def _sell_aircraft(self):
        serial = self._get_selected_serial()
        if serial is None:
            return
        owned = self.state.get_owned(serial)
        if not owned:
            return
        if not messagebox.askyesno('Confirm Sale', f'Sell {owned.name}?', parent=self):
            return
        ok, msg = self.engine.sell_aircraft(serial)
        if ok:
            messagebox.showinfo('Sold', msg, parent=self)
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()
        else:
            messagebox.showerror('Cannot Sell', msg, parent=self)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES PANEL
# ─────────────────────────────────────────────────────────────────────────────
class RoutesPanel(tk.Frame):
    def __init__(self, parent, state, engine: GameEngine, on_map_refresh=None, refresh_cb=None, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self.engine = engine
        self.on_map_refresh = on_map_refresh
        self.refresh_cb = refresh_cb
        self._origin = None
        self._build()

    def _build(self):
        # Top: open new route
        top = tk.Frame(self, bg=BG3)
        top.pack(fill='x', padx=8, pady=8)

        tk.Label(top, text='OPEN NEW ROUTE', fg=GOLD, bg=BG3, font=F_SUBHEAD).grid(
            row=0, column=0, columnspan=6, sticky='w', padx=10, pady=(8,4))

        tk.Label(top, text='Origin:', fg=TEXT2, bg=BG3, font=F_SMALL).grid(
            row=1, column=0, padx=(10,2), pady=4)
        self._orig_var = tk.StringVar()
        orig_cb = ttk.Combobox(top, textvariable=self._orig_var, width=10,
                                values=sorted([c.code for c in CITIES]),
                                state='readonly', font=F_SMALL)
        orig_cb.grid(row=1, column=1, padx=2, pady=4)

        tk.Label(top, text='→', fg=ACCENT2, bg=BG3, font=F_HEAD).grid(
            row=1, column=2, padx=4)

        tk.Label(top, text='Dest:', fg=TEXT2, bg=BG3, font=F_SMALL).grid(
            row=1, column=3, padx=(2,2), pady=4)
        self._dest_var = tk.StringVar()
        dest_cb = ttk.Combobox(top, textvariable=self._dest_var, width=10,
                                values=sorted([c.code for c in CITIES]),
                                state='readonly', font=F_SMALL)
        dest_cb.grid(row=1, column=4, padx=2, pady=4)

        icon_btn(top, '➕  Open Route', self._open_route,
                 color=GREEN, font=F_SMALL).grid(row=1, column=5, padx=10, pady=4)

        tk.Label(top, text='💡 Tip: Click cities on the map to auto-fill origin/destination',
                 fg=MUTED, bg=BG3, font=F_SMALL).grid(
                 row=2, column=0, columnspan=6, sticky='w', padx=10, pady=(0,6))

        # Route list
        tk.Label(self, text='YOUR ROUTES', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(4, 2))

        frame = tk.Frame(self, bg=BG2)
        frame.pack(fill='both', expand=True, padx=8, pady=4)

        cols = ('id','origin','dest','dist','aircraft','weekly_pax','ticket','status')
        self._tree = ttk.Treeview(frame, columns=cols, show='headings',
                                   selectmode='browse', style='Treeview')
        hdrs = [('id','Route',100),('origin','From',55),('dest','To',55),
                ('dist','Distance',90),('aircraft','Aircraft',60),
                ('weekly_pax','Wk Pax',70),('ticket','Ticket',75),('status','Status',80)]
        for col, hdr, w in hdrs:
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=w, anchor='center')
        self._tree.column('id', anchor='w')

        sb = ttk.Scrollbar(frame, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        btn_row = tk.Frame(self, bg=BG2)
        btn_row.pack(fill='x', padx=8, pady=4)
        icon_btn(btn_row, '💰  Set Ticket Price', self._set_price,
                 color=ACCENT, font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '🗑  Close Route', self._close_route,
                 color='#5a1a1a', font=F_SMALL).pack(side='left', padx=2)

        self.refresh()

    def set_city(self, city_code: str):
        """Called from map click to fill origin/dest fields."""
        if not self._orig_var.get():
            self._orig_var.set(city_code)
        elif not self._dest_var.get():
            self._dest_var.set(city_code)
        else:
            self._orig_var.set(city_code)
            self._dest_var.set('')

    def refresh(self):
        sel = self._tree.selection()  # preserve selection across refresh
        for item in self._tree.get_children():
            self._tree.delete(item)
        for route in self.state.routes:
            n_ac = len(route.aircraft_ids)
            status = '🟢 Active' if n_ac > 0 else '🔴 No AC'
            tag = 'active' if n_ac > 0 else 'idle'
            self._tree.insert('', 'end', iid=route.id,
                values=(route.id, route.origin, route.dest,
                        f'{route.distance_km:,.0f}km', n_ac,
                        f'{route.weekly_pax:,}', f'${route.ticket_price:.0f}', status),
                tags=(tag,))
        self._tree.tag_configure('active', foreground=GREEN)
        self._tree.tag_configure('idle', foreground=TEXT2)
        for iid in sel:
            if self._tree.exists(iid):
                self._tree.selection_set(iid)

    def _open_route(self):
        orig = self._orig_var.get().strip().upper()
        dest = self._dest_var.get().strip().upper()
        if not orig or not dest:
            messagebox.showwarning('Missing Fields', 'Select both origin and destination.', parent=self)
            return
        ok, msg = self.engine.open_route(orig, dest)
        if ok:
            if self.on_map_refresh:
                self.on_map_refresh()
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()
            self._orig_var.set('')
            self._dest_var.set('')
        else:
            messagebox.showerror('Cannot Open Route', msg, parent=self)

    def _close_route(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning('Select Route', 'Select a route to close.', parent=self)
            return
        rid = sel[0]
        if not messagebox.askyesno('Confirm', f'Close route {rid}?', parent=self):
            return
        ok, msg = self.engine.close_route(rid)
        if ok:
            if self.on_map_refresh:
                self.on_map_refresh()
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()

    def _set_price(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning('Select Route', 'Select a route first.', parent=self)
            return
        rid = sel[0]
        route = self.state.get_route(rid)
        if not route:
            return
        price = simpledialog.askfloat('Ticket Price',
            f'Set ticket price for {rid} (current: ${route.ticket_price:.0f})\n'
            f'Route distance: {route.distance_km:.0f} km\n'
            f'Tip: Lower prices attract more passengers.',
            minvalue=10, maxvalue=10000, parent=self)
        if price:
            route.ticket_price = price
            self.refresh()


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE PANEL
# ─────────────────────────────────────────────────────────────────────────────
class FinancePanel(tk.Frame):
    def __init__(self, parent, state, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self._build()

    def _build(self):
        # Top stats row
        stats = tk.Frame(self, bg=BG2)
        stats.pack(fill='x', padx=8, pady=8)

        self._stat_widgets = {}
        for i, (label, key, color) in enumerate([
            ('CASH',      'cash',    GOLD),
            ('NET WORTH', 'worth',   ACCENT2),
            ('TOTAL PAX', 'pax',     GREEN),
            ('REPUTATION','rep',     TEXT),
        ]):
            card = tk.Frame(stats, bg=BG3, padx=16, pady=10)
            card.grid(row=0, column=i, sticky='nsew', padx=4)
            stats.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=label, fg=TEXT2, bg=BG3, font=F_SMALL).pack()
            val_lbl = tk.Label(card, text='—', fg=color, bg=BG3, font=F_MED_NUM)
            val_lbl.pack()
            self._stat_widgets[key] = val_lbl

        # Chart canvas
        tk.Label(self, text='MONTHLY PERFORMANCE', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(8,2))

        self._chart = tk.Canvas(self, bg=BG3, height=180, highlightthickness=0)
        self._chart.pack(fill='x', padx=8, pady=4)

        # History table
        tk.Label(self, text='FINANCIAL HISTORY', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(8,2))

        frm = tk.Frame(self, bg=BG2)
        frm.pack(fill='both', expand=True, padx=8, pady=4)

        cols = ('period','revenue','costs','profit','cash')
        self._tree = ttk.Treeview(frm, columns=cols, show='headings',
                                   selectmode='none', style='Treeview')
        hdrs = [('period','Month',80),('revenue','Revenue',100),
                ('costs','Costs',100),('profit','Profit/Loss',110),('cash','Cash',110)]
        for col, hdr, w in hdrs:
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=w, anchor='center')

        sb = ttk.Scrollbar(frm, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        self.refresh()

    def refresh(self):
        s = self.state
        self._stat_widgets['cash'].config(text=money_str(s.cash))
        self._stat_widgets['worth'].config(text=money_str(s.net_worth))
        self._stat_widgets['pax'].config(text=pax_str(s.total_pax))
        self._stat_widgets['rep'].config(text=f'{s.reputation:.0f}/100')

        for item in self._tree.get_children():
            self._tree.delete(item)
        _MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']
        for rec in reversed(s.finance_history[-40:]):
            tag = 'profit' if rec.profit >= 0 else 'loss'
            month_name = _MONTHS[rec.month - 1] if 1 <= rec.month <= 12 else f'M{rec.month}'
            self._tree.insert('', 'end',
                values=(f'{month_name} {rec.year}',
                        money_str(rec.revenue), money_str(rec.costs),
                        money_str(rec.profit), money_str(rec.cash_end)),
                tags=(tag,))
        self._tree.tag_configure('profit', foreground=GREEN)
        self._tree.tag_configure('loss',   foreground=RED)

        self._draw_chart()

    def _draw_chart(self):
        c = self._chart
        c.delete('all')
        w = c.winfo_width() or 600
        h = 180
        pad = 50

        history = self.state.finance_history[-20:]
        if not history:
            c.create_text(w//2, h//2, text='No data yet — let some time pass!',
                           fill=MUTED, font=F_SMALL)
            return

        rev_vals = [r.revenue for r in history]
        cost_vals = [r.costs for r in history]
        all_vals = rev_vals + cost_vals
        mn = min(all_vals + [0])
        mx = max(all_vals + [0.01])

        def vy(v):
            return h - pad - (v - mn) / (mx - mn) * (h - 2*pad) if mx > mn else h//2

        # Zero line
        y0 = vy(0)
        c.create_line(pad, y0, w-pad, y0, fill=BORDER, dash=(4, 4))

        n = len(history)
        def vx(i):
            return pad + i / max(1, n-1) * (w - 2*pad)

        # Revenue bars
        bar_w = max(3, (w - 2*pad) / max(1, n) - 2)
        for i, rec in enumerate(history):
            x = vx(i)
            y_r = vy(rec.revenue)
            y_c = vy(rec.costs)
            # Revenue bar
            c.create_rectangle(x - bar_w/2, y_r, x, y0,
                                 fill=ACCENT, outline='', stipple='')
            # Cost bar
            c.create_rectangle(x, y_c, x + bar_w/2, y0,
                                 fill='#8b2222', outline='')

        # Profit line
        pts = []
        for i, rec in enumerate(history):
            pts.extend([vx(i), vy(rec.profit)])
        if len(pts) >= 4:
            c.create_line(*pts, fill=GOLD, width=2, smooth=True)

        # Labels
        c.create_text(pad-2, vy(mx), text=money_str(mx), fill=TEXT2, font=F_SMALL, anchor='e')
        c.create_text(pad-2, vy(mn), text=money_str(mn), fill=TEXT2, font=F_SMALL, anchor='e')
        c.create_text(pad+5, 8, text='■ Revenue', fill=ACCENT, font=F_SMALL, anchor='w')
        c.create_text(pad+90, 8, text='■ Costs', fill='#e05050', font=F_SMALL, anchor='w')
        c.create_text(pad+170, 8, text='— Profit', fill=GOLD, font=F_SMALL, anchor='w')


# ─────────────────────────────────────────────────────────────────────────────
# EVENTS PANEL
# ─────────────────────────────────────────────────────────────────────────────
class EventsPanel(tk.Frame):
    def __init__(self, parent, state, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self._build()

    def _build(self):
        tk.Label(self, text='NEWS & EVENTS LOG', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(10,4))

        frame = tk.Frame(self, bg=BG2)
        frame.pack(fill='both', expand=True, padx=8, pady=4)
        sb = tk.Scrollbar(frame, bg=BG2)
        sb.pack(side='right', fill='y')
        self._text = tk.Text(frame, bg=BG3, fg=TEXT, font=F_BODY, state='disabled',
                              relief='flat', yscrollcommand=sb.set,
                              selectbackground=SEL, insertbackground=TEXT,
                              wrap='word', padx=10, pady=8, spacing3=4)
        self._text.pack(side='left', fill='both', expand=True)
        sb.config(command=self._text.yview)

        self._text.tag_configure('event', foreground=ORANGE, font=(_SANS if True else 'Helvetica', 11, 'bold'))
        self._text.tag_configure('news', foreground=TEXT)
        self._text.tag_configure('info', foreground=TEXT2)

        # Aviation timeline
        tk.Label(self, text='AVIATION TIMELINE', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(8,2))
        self._timeline = ttk.Treeview(self, columns=('year','event'), show='headings',
                                       height=8, style='Treeview')
        self._timeline.heading('year', text='Year')
        self._timeline.heading('event', text='Historical Event')
        self._timeline.column('year', width=60, anchor='center')
        self._timeline.column('event', width=400, anchor='w')
        self._timeline.pack(fill='x', padx=8, pady=4)

        from engine import HISTORICAL_EVENTS
        for yr, desc, _, _ in HISTORICAL_EVENTS:
            past = yr <= self.state.year
            self._timeline.insert('', 'end', values=(yr, desc),
                                   tags=('past' if past else 'future',))
        self._timeline.tag_configure('past', foreground=TEXT2)
        self._timeline.tag_configure('future', foreground=MUTED)

        self.refresh()

    def refresh(self):
        self._text.config(state='normal')
        self._text.delete('1.0', 'end')
        for entry in reversed(self.state.events_log):
            tag = 'event' if '📰' in entry else ('info' if '🛫' in entry else 'news')
            self._text.insert('end', entry + '\n', tag)
        self._text.config(state='disabled')
        self._text.see('1.0')

_SANS = 'Helvetica'
