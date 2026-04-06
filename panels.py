"""Game panels: Fleet, Routes, Finance, Events, Research"""
import tkinter as tk
from tkinter import ttk, messagebox
import math
from ui_theme import *
from data import AIRCRAFT_DB, CITY_DICT, CITIES, get_aircraft, available_aircraft
from engine import (GameEngine, RESEARCH_PROJECTS, CABIN_MULTIPLIERS,
                    CABIN_DISPLAY_NAMES, CABIN_DEMAND_FRACTIONS, CABIN_SEAT_SIZES)

# ─────────────────────────────────────────────────────────────────────────────
# FLEET PANEL
# ─────────────────────────────────────────────────────────────────────────────
class FleetPanel(tk.Frame):
    def __init__(self, parent, state, engine: GameEngine, refresh_cb=None, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self.engine = engine
        self.refresh_cb = refresh_cb
        self._hidden_aircraft: set = set()   # aircraft ids hidden from the market
        self._show_hidden = False
        self._build()

    def _build(self):
        # Left: owned aircraft (packed LAST so expand=True doesn't steal space from fixed-width right panels)
        left = tk.Frame(self, bg=BG2)

        tk.Label(left, text='YOUR FLEET', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(10, 4))

        cols = ('name','type','cabin','range','condition','route','age')
        self._fleet_tree = ttk.Treeview(left, columns=cols, show='headings',
                                         selectmode='browse', style='Treeview')
        hdrs = [('name','Aircraft',180),('type','Class',65),
                ('cabin','Cabin Layout',120),('range','Range',90),
                ('condition','Cond.',60),('route','Route',90),('age','Age',40)]
        for col, hdr, w in hdrs:
            self._fleet_tree.heading(col, text=hdr)
            self._fleet_tree.column(col, width=w, anchor='center')
        self._fleet_tree.column('name', anchor='w')

        # btn_row must be packed with side='bottom' BEFORE the tree claims all space
        btn_row = tk.Frame(left, bg=BG2)
        btn_row.pack(side='bottom', fill='x', padx=8, pady=4)
        icon_btn(btn_row, '✈  Assign to Route', self._assign_route,
                 color=ACCENT, font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '⬛  Remove from Route', self._remove_route,
                 color='#1a3050', font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '🪑  Configure Cabin', self._configure_cabin,
                 color='#1a4a2a', font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '💛  Toggle Budget', self._toggle_budget,
                 color='#4a3a00', font=F_SMALL).pack(side='left', padx=2)
        icon_btn(btn_row, '💰  Sell Aircraft', self._sell_aircraft,
                 color='#5a1a1a', font=F_SMALL).pack(side='left', padx=2)

        sb = ttk.Scrollbar(left, orient='vertical', command=self._fleet_tree.yview)
        self._fleet_tree.configure(yscrollcommand=sb.set)
        self._fleet_tree.pack(side='left', fill='both', expand=True, padx=(8,0), pady=4)
        sb.pack(side='left', fill='y', pady=4)

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

        # Right: marketplace (packed before left so it claims its fixed width first)
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
        self._hide_btn = icon_btn(filt, '🙈 Hide', self._hide_selected,
                                  color='#3a3a3a', font=F_SMALL, padx=6, pady=2)
        self._hide_btn.pack(side='left', padx=(8, 2))
        self._show_hidden_btn = icon_btn(filt, 'Show Hidden', self._toggle_show_hidden,
                                         color=MUTED, font=F_SMALL, padx=6, pady=2)
        self._show_hidden_btn.pack(side='left', padx=2)

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
        self._market_tree.bind('<Button-3>', self._on_market_right_click)

        sb2 = ttk.Scrollbar(right, orient='vertical', command=self._market_tree.yview)
        self._market_tree.configure(yscrollcommand=sb2.set)
        self._market_tree.pack(side='left', fill='both', expand=True, padx=(8,0), pady=4)
        sb2.pack(side='left', fill='y', pady=4)

        # Pack left LAST so expand=True only consumes remaining space after right panels claimed theirs
        left.pack(side='left', fill='both', expand=True, padx=(0, 2))

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
            rng = f'{ac.range_km:,}km' if ac else '?'
            cond = f'{owned.condition*100:.0f}%'
            route = owned.assigned_route or '—'
            age = self.state.year - owned.year_acquired
            # Cabin layout summary: e.g. "💛E320 / B24 / F8" (💛 = budget mode)
            cabin = owned.cabin_config or ({'economy': ac.passengers} if ac else {})
            _short = {'economy': 'E', 'premium_economy': 'P', 'business': 'B',
                      'first': 'F', 'supersonic_first': 'S'}
            cabin_str = ' / '.join(
                f'{_short.get(cls, cls[0].upper())}{seats}'
                for cls, seats in cabin.items() if seats > 0
            ) or '—'
            if owned.is_budget:
                cabin_str = '💛 ' + cabin_str
            tag = 'good' if owned.condition > 0.7 else ('warn' if owned.condition > 0.4 else 'bad')
            self._fleet_tree.insert('', 'end',
                iid=str(owned.serial),
                values=(owned.name, cat, cabin_str, rng, cond, route, age),
                tags=(tag,))
        self._fleet_tree.tag_configure('good', foreground=TEXT)
        self._fleet_tree.tag_configure('warn', foreground=ORANGE)
        self._fleet_tree.tag_configure('bad',  foreground=RED)
        for iid in sel:
            if self._fleet_tree.exists(iid):
                self._fleet_tree.selection_set(iid)

    @staticmethod
    def _retirement_year(ac) -> int:
        """Estimate the year a type was taken out of new production."""
        # Pioneer/regional props: short production run
        if ac.category == 'pioneer':
            return ac.year + 20
        if ac.category in ('regional', 'narrow', 'wide') and ac.year < 1950:
            return ac.year + 30
        if ac.year < 1970:
            return ac.year + 40
        if ac.year < 1990:
            return ac.year + 45
        return 9999  # modern types still in production

    def _hide_selected(self):
        sel = self._market_tree.selection()
        if sel:
            self._hidden_aircraft.add(sel[0])
            self._populate_market()

    def _toggle_show_hidden(self):
        self._show_hidden = not self._show_hidden
        self._show_hidden_btn.config(
            text='Hide Hidden' if self._show_hidden else 'Show Hidden',
            bg=ACCENT if self._show_hidden else MUTED)
        self._populate_market()

    def _on_market_right_click(self, event):
        row = self._market_tree.identify_row(event.y)
        if not row:
            return
        self._market_tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0, bg=BG2, fg=TEXT,
                       activebackground=SEL, activeforeground=WHITE)
        if row in self._hidden_aircraft:
            menu.add_command(label='Unhide aircraft',
                             command=lambda: (self._hidden_aircraft.discard(row),
                                              self._populate_market()))
        else:
            menu.add_command(label='Hide aircraft',
                             command=lambda: (self._hidden_aircraft.add(row),
                                              self._populate_market()))
        menu.tk_popup(event.x_root, event.y_root)

    def _populate_market(self):
        sel = self._market_tree.selection()
        for item in self._market_tree.get_children():
            self._market_tree.delete(item)
        cat_filter = self._cat_var.get()
        year = self.state.year
        for ac in AIRCRAFT_DB:
            if cat_filter != 'All' and ac.category != cat_filter:
                continue
            retired = self._retirement_year(ac) < year
            hidden = ac.id in self._hidden_aircraft
            # Retired planes: skip entirely (out of production)
            if retired:
                continue
            # Hidden planes: skip unless showing hidden
            if hidden and not self._show_hidden:
                continue
            avail = ac.year <= year
            if hidden:
                tag = 'hidden'
            elif avail:
                tag = 'avail'
            else:
                tag = 'future'
            yr_str = str(ac.year) if not avail else '✓'
            speed_str = f'M{ac.speed_kmh/1225:.1f}' if ac.speed_kmh > 1200 else f'{ac.speed_kmh}km/h'
            self._market_tree.insert('', 'end', iid=ac.id,
                values=(ac.name, yr_str, ac.passengers,
                        f'{ac.range_km:,}km' if ac.range_km > 0 else 'Orbital',
                        speed_str, money_str(ac.cost_m * 1_000_000)),
                tags=(tag,))
        self._market_tree.tag_configure('avail',  foreground=TEXT)
        self._market_tree.tag_configure('future', foreground=MUTED)
        self._market_tree.tag_configure('hidden', foreground='#5a3a5a')
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
        affordable = int(ac.cost_m * 1_000_000) <= self.state.cash
        fuel_icons = {'jet':'⛽','avgas':'🛢','hydrogen':'💧','electric':'⚡','saf':'🌱','methane':'🔥'}
        fuel_icon = fuel_icons.get(ac.fuel_type, '⛽')
        cat_icons = {'pioneer':'🪂','regional':'🛩','narrow':'✈','wide':'🛫',
                     'supersonic':'🚀','future':'🔮'}
        cat_icon = cat_icons.get(ac.category, '✈')
        speed_str = f'Mach {ac.speed_kmh/1225:.1f}' if ac.speed_kmh > 1200 else f'{ac.speed_kmh} km/h'
        range_str = 'Suborbital' if ac.range_km <= 0 else f'{ac.range_km:,} km'
        status = '✅ Available' if avail else f'🔒 Available {ac.year}'
        cost_color = GREEN if affordable else RED
        sep = '─' * 28
        details = (
            f'{cat_icon} {ac.name}\n'
            f'{sep}\n'
            f'🏭  {ac.manufacturer}\n'
            f'📅  {ac.year} · {status}\n\n'
            f'👥  {ac.passengers} passengers\n'
            f'📏  {range_str}\n'
            f'💨  {speed_str}\n'
            f'{fuel_icon}  {ac.fuel_type.title()} propulsion\n\n'
            f'💰  {money_str(ac.cost_m * 1_000_000)}\n'
            f'🔧  {money_str(ac.monthly_cost_k * 1000)}/month ops\n\n'
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
        ac = self._selected_ac
        cost = int(ac.cost_m * 1_000_000)
        cash_after = self.state.cash - cost

        if cash_after < 0:
            messagebox.showerror('Cannot Purchase',
                f'Not enough cash.\nNeed {money_str(cost)}, have {money_str(int(self.state.cash))}.',
                parent=self)
            return

        # Skip confirmation dialog on Easy and Normal difficulty
        diff = getattr(self.state, 'difficulty', 'normal')
        if diff in ('easy', 'normal'):
            confirmed = True
        else:
            monthly = int(ac.monthly_cost_k * 1000)
            confirmed = messagebox.askyesno('Confirm Purchase',
                f'Purchase {ac.name}?\n\n'
                f'  Cost:            {money_str(cost)}\n'
                f'  Cash after:   {money_str(cash_after)}\n'
                f'  Monthly ops: {money_str(monthly)}/mo\n'
                f'  Seats:           {ac.passengers}  ·  Range: {ac.range_km:,} km',
                parent=self)

        if confirmed:
            ok, msg = self.engine.buy_aircraft(ac)
            if ok:
                # Find the just-purchased aircraft (last in fleet)
                new_owned = self.state.fleet[-1] if self.state.fleet else None
                if self.refresh_cb:
                    self.refresh_cb()
                self.refresh()
                # If premium cabins are unlocked, offer cabin configuration right away
                if new_owned and len(self.engine.unlocked_cabin_classes()) > 1:
                    # Temporarily set selection so _configure_cabin works
                    self._fleet_tree.selection_set(str(new_owned.serial))
                    self._configure_cabin()
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

        # Route picker dialog — withdraw first so the WM doesn't map an
        # empty frame; build widgets while hidden, then deiconify.
        result = [None]
        dlg = tk.Toplevel(self)
        dlg.withdraw()
        dlg.title('Assign Route')
        dlg.configure(bg=BG2)
        dlg.transient(self.winfo_toplevel())

        tk.Label(dlg, text='Select a route:', fg=TEXT, bg=BG2, font=F_SMALL).pack(
            padx=12, pady=(10, 4), anchor='w')

        lb = tk.Listbox(dlg, bg=BG3, fg=TEXT, selectbackground=ACCENT,
                        font=F_SMALL, width=40,
                        height=min(max(len(self.state.routes), 1), 12),
                        activestyle='none', exportselection=0)
        for r in self.state.routes:
            lb.insert('end', f'{r.id}  —  {r.distance_km:.0f} km')
        lb.pack(padx=12, pady=4, fill='x')
        lb.selection_set(0)

        def on_assign():
            sel = lb.curselection()
            if sel:
                result[0] = self.state.routes[sel[0]].id
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=BG2)
        btn_row.pack(pady=8)
        icon_btn(btn_row, 'Assign', on_assign, color=ACCENT, font=F_SMALL).pack(side='left', padx=4)
        icon_btn(btn_row, 'Cancel', dlg.destroy, color='#3a3a3a', font=F_SMALL).pack(side='left', padx=4)

        # Compute natural size while hidden, then show centred over parent
        dlg.update_idletasks()
        pw = self.winfo_toplevel()
        x = pw.winfo_rootx() + (pw.winfo_width() - dlg.winfo_reqwidth()) // 2
        y = pw.winfo_rooty() + (pw.winfo_height() - dlg.winfo_reqheight()) // 2
        dlg.geometry(f'{dlg.winfo_reqwidth()}x{dlg.winfo_reqheight()}+{x}+{y}')
        dlg.resizable(False, False)
        dlg.deiconify()
        dlg.grab_set()

        dlg.wait_window()

        rid = result[0]
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

    def _toggle_budget(self):
        serial = self._get_selected_serial()
        if serial is None:
            return
        ok, msg = self.engine.toggle_budget(serial)
        if ok:
            self.refresh()
            if self.refresh_cb:
                self.refresh_cb()
        else:
            messagebox.showwarning('Budget Mode', msg, parent=self)

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

    def _configure_cabin(self):
        serial = self._get_selected_serial()
        if serial is None:
            return
        owned = self.state.get_owned(serial)
        if not owned:
            return
        ac = get_aircraft(owned.ac_id)
        if not ac:
            return

        unlocked = self.engine.unlocked_cabin_classes()
        capacity = ac.passengers
        current = owned.cabin_config or {'economy': capacity}

        dlg = tk.Toplevel(self)
        dlg.withdraw()
        dlg.title(f'Cabin Configuration — {owned.name}')
        dlg.configure(bg=BG2)
        dlg.transient(self.winfo_toplevel())
        dlg.resizable(False, False)

        tk.Label(dlg, text=f'Configure cabin for {owned.name}',
                 fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(padx=16, pady=(12, 2))
        tk.Label(dlg,
                 text=f'Aircraft has {capacity} seat-units of space.\n'
                      f'PE=1.5×, Business=2.5×, First=4× the space of Economy.',
                 fg=TEXT2, bg=BG2, font=F_SMALL, justify='left').pack(padx=16, pady=(0, 8))

        # Class rows
        _class_order = ['economy', 'premium_economy', 'business', 'first', 'supersonic_first']
        _class_colors = {
            'economy': TEXT2,
            'premium_economy': ACCENT2,
            'business': GOLD,
            'first': '#d4a0e8',
            'supersonic_first': RED,
        }
        vars_map: dict = {}

        grid = tk.Frame(dlg, bg=BG2)
        grid.pack(padx=16, pady=4, fill='x')

        header_cols = ['Cabin Class', 'Seats', 'Revenue Mult.', 'Status']
        for c, h in enumerate(header_cols):
            tk.Label(grid, text=h, fg=MUTED, bg=BG2, font=F_SMALL).grid(
                row=0, column=c, padx=8, pady=2, sticky='w')

        for row_i, cls in enumerate(_class_order, start=1):
            is_unlocked = cls in unlocked
            is_supersonic_only = cls == 'supersonic_first'
            is_applicable = is_unlocked and (not is_supersonic_only or ac.category == 'supersonic')

            color = _class_colors.get(cls, TEXT)
            name = CABIN_DISPLAY_NAMES.get(cls, cls)
            mult = CABIN_MULTIPLIERS.get(cls, 1.0)

            tk.Label(grid, text=name, fg=color if is_applicable else MUTED,
                     bg=BG2, font=F_SMALL, width=18, anchor='w').grid(
                row=row_i, column=0, padx=8, pady=3, sticky='w')

            var = tk.IntVar(value=current.get(cls, 0) if is_applicable else 0)
            vars_map[cls] = var
            max_for_class = int(capacity / CABIN_SEAT_SIZES.get(cls, 1.0))
            spin = tk.Spinbox(grid, from_=0, to=max_for_class, textvariable=var,
                              width=6, bg=BG3, fg=color if is_applicable else MUTED,
                              buttonbackground=BG3, insertbackground=TEXT,
                              font=F_SMALL, state='normal' if is_applicable else 'disabled',
                              relief='flat')
            spin.grid(row=row_i, column=1, padx=8, pady=3)

            tk.Label(grid, text=f'{mult:.1f}×', fg=color if is_applicable else MUTED,
                     bg=BG2, font=F_SMALL).grid(row=row_i, column=2, padx=8, pady=3)

            if not is_unlocked:
                status = '🔒 Research required'
            elif is_supersonic_only and ac.category != 'supersonic':
                status = '🚀 Supersonic only'
            else:
                status = '✅ Available'
            tk.Label(grid, text=status, fg=MUTED if not is_applicable else GREEN,
                     bg=BG2, font=F_SMALL).grid(row=row_i, column=3, padx=8, pady=3, sticky='w')

        # Total indicator
        sep_frame = tk.Frame(dlg, bg=BORDER, height=1)
        sep_frame.pack(fill='x', padx=16, pady=4)

        total_lbl = tk.Label(dlg, text='', fg=TEXT, bg=BG2, font=F_SMALL)
        total_lbl.pack(padx=16, pady=2)

        def _safe_get(var):
            try:
                return max(0, int(var.get()))
            except (tk.TclError, ValueError):
                return 0

        def update_total(*_):
            units = sum(_safe_get(v) * CABIN_SEAT_SIZES.get(cls, 1.0)
                        for cls, v in vars_map.items())
            remaining = capacity - units
            if units > capacity:
                total_lbl.config(
                    text=f'⚠  Space used: {units:.0f} / {capacity}  — {units-capacity:.0f} over limit!',
                    fg=RED)
            elif remaining > 0.5:
                total_lbl.config(
                    text=f'Space used: {units:.0f} / {capacity}  — {remaining:.0f} units → Economy',
                    fg=ORANGE)
            else:
                total_lbl.config(text=f'Space used: {units:.0f} / {capacity}  ✓', fg=GREEN)

        for var in vars_map.values():
            var.trace_add('write', update_total)
        update_total()

        def on_save():
            config = {cls: _safe_get(v) for cls, v in vars_map.items()}
            # Fill remaining space with economy seats
            used_units = sum(v * CABIN_SEAT_SIZES.get(c, 1.0) for c, v in config.items())
            leftover_units = capacity - used_units
            if leftover_units >= 1.0:
                config['economy'] = config.get('economy', 0) + int(leftover_units)
            if config.get('economy', 0) < 0:
                config['economy'] = 0
            ok, msg = self.engine.configure_cabin(serial, config)
            if ok:
                dlg.destroy()
                self.refresh()
                if self.refresh_cb:
                    self.refresh_cb()
            else:
                messagebox.showerror('Invalid Configuration', msg, parent=dlg)

        btn_row = tk.Frame(dlg, bg=BG2)
        btn_row.pack(pady=10)
        icon_btn(btn_row, '💾  Save Configuration', on_save,
                 color=GREEN, font=F_SMALL).pack(side='left', padx=4)
        icon_btn(btn_row, 'Cancel', dlg.destroy,
                 color='#3a3a3a', font=F_SMALL).pack(side='left', padx=4)

        dlg.update_idletasks()
        pw = self.winfo_toplevel()
        x = pw.winfo_rootx() + (pw.winfo_width() - dlg.winfo_reqwidth()) // 2
        y = pw.winfo_rooty() + (pw.winfo_height() - dlg.winfo_reqheight()) // 2
        dlg.geometry(f'{dlg.winfo_reqwidth()}x{dlg.winfo_reqheight()}+{x}+{y}')
        dlg.deiconify()
        dlg.grab_set()
        dlg.wait_window()


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

        tk.Label(top, text='OPEN NEW ROUTE', fg=GOLD, bg=BG3, font=F_SUBHEAD).pack(
            anchor='w', padx=10, pady=(8, 4))

        # Dynamic stop list
        self._stop_vars = [tk.StringVar(), tk.StringVar()]
        self._stops_frame = tk.Frame(top, bg=BG3)
        self._stops_frame.pack(fill='x', padx=10, pady=2)
        self._render_stops()

        btn_row = tk.Frame(top, bg=BG3)
        btn_row.pack(anchor='w', padx=10, pady=(4, 6))
        icon_btn(btn_row, '➕ Add Stop', self._add_stop,
                 color=ACCENT, font=F_SMALL, padx=8, pady=3).pack(side='left', padx=(0, 6))
        icon_btn(btn_row, '✈  Open Route', self._open_route,
                 color=GREEN, font=F_SMALL, padx=10, pady=3).pack(side='left')

        tk.Label(top, text='💡 Tip: Click cities on the map to auto-fill stops',
                 fg=MUTED, bg=BG3, font=F_SMALL).pack(anchor='w', padx=10, pady=(0, 6))

        # Route list
        tk.Label(self, text='YOUR ROUTES', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(4, 2))

        frame = tk.Frame(self, bg=BG2)
        frame.pack(fill='both', expand=True, padx=8, pady=4)

        cols = ('stops', 'dist', 'legs', 'aircraft', 'weekly_pax', 'ticket', 'rev_trip', 'status')
        self._tree = ttk.Treeview(frame, columns=cols, show='headings',
                                   selectmode='browse', style='Treeview')
        hdrs = [('stops', 'Route', 200), ('dist', 'Distance', 90), ('legs', 'Legs', 45),
                ('aircraft', 'Aircraft', 60), ('weekly_pax', 'Wk Pax', 70),
                ('ticket', 'Ticket', 70), ('rev_trip', 'Rev/Trip', 90), ('status', 'Status', 80)]
        for col, hdr, w in hdrs:
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=w, anchor='center')
        self._tree.column('stops', anchor='w')

        sb = ttk.Scrollbar(frame, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        route_btn_row = tk.Frame(self, bg=BG2)
        route_btn_row.pack(fill='x', padx=8, pady=4)
        icon_btn(route_btn_row, '💰  Set Ticket Price', self._set_price,
                 color=ACCENT, font=F_SMALL).pack(side='left', padx=2)
        icon_btn(route_btn_row, '🗑  Close Route', self._close_route,
                 color='#5a1a1a', font=F_SMALL).pack(side='left', padx=2)

        # Assigned planes sub-list
        tk.Label(self, text='ASSIGNED AIRCRAFT', fg=GOLD, bg=BG2, font=F_SUBHEAD).pack(
            anchor='w', padx=12, pady=(8, 2))

        ac_frame = tk.Frame(self, bg=BG2)
        ac_frame.pack(fill='x', padx=8, pady=(0, 8))

        ac_cols = ('name', 'condition', 'hours', 'revenue', 'status')
        self._ac_tree = ttk.Treeview(ac_frame, columns=ac_cols, show='headings',
                                      selectmode='none', style='Treeview', height=5)
        ac_hdrs = [('name', 'Aircraft', 160), ('condition', 'Cond.', 60),
                   ('hours', 'Hours', 70), ('revenue', 'Rev/Trip', 90),
                   ('status', 'Status', 100)]
        for col, hdr, w in ac_hdrs:
            self._ac_tree.heading(col, text=hdr)
            self._ac_tree.column(col, width=w, anchor='center')
        self._ac_tree.column('name', anchor='w')

        ac_sb = ttk.Scrollbar(ac_frame, orient='vertical', command=self._ac_tree.yview)
        self._ac_tree.configure(yscrollcommand=ac_sb.set)
        self._ac_tree.pack(side='left', fill='x', expand=True)
        ac_sb.pack(side='right', fill='y')

        self._tree.bind('<<TreeviewSelect>>', self._on_route_select)

        self.refresh()

    def _render_stops(self):
        for w in self._stops_frame.winfo_children():
            w.destroy()
        city_codes = sorted([c.code for c in CITIES])
        for i, sv in enumerate(self._stop_vars):
            row = tk.Frame(self._stops_frame, bg=BG3)
            row.pack(anchor='w', pady=1)
            if i > 0:
                tk.Label(row, text='→', fg=ACCENT2, bg=BG3, font=F_SUBHEAD).pack(
                    side='left', padx=(0, 4))
            else:
                tk.Label(row, text='   ', bg=BG3).pack(side='left')  # indent align
            ttk.Combobox(row, textvariable=sv, width=10, values=city_codes,
                         state='readonly', font=F_SMALL).pack(side='left', padx=2)
            if len(self._stop_vars) > 2:
                def _make_remove(idx=i):
                    def _remove():
                        self._stop_vars.pop(idx)
                        self._render_stops()
                    return _remove
                icon_btn(row, '✕', _make_remove(), color='#5a1a1a',
                         font=F_SMALL, padx=5, pady=1).pack(side='left', padx=3)

    def _add_stop(self):
        if len(self._stop_vars) < 8:
            self._stop_vars.append(tk.StringVar())
            self._render_stops()

    def set_city(self, city_code: str):
        """Called from map click — fills next empty stop slot, or appends a new one."""
        for sv in self._stop_vars:
            if not sv.get():
                sv.set(city_code)
                return
        if len(self._stop_vars) < 8:
            self._stop_vars.append(tk.StringVar(value=city_code))
            self._render_stops()

    def refresh(self):
        sel = self._tree.selection()  # preserve selection across refresh
        for item in self._tree.get_children():
            self._tree.delete(item)
        for route in self.state.routes:
            n_ac = len(route.aircraft_ids)
            status = '🟢 Active' if n_ac > 0 else '🔴 No AC'
            tag = 'active' if n_ac > 0 else 'idle'
            rev_str = money_str(route.last_revenue) if route.last_revenue > 0 else '—'
            stops_str = '→'.join(route.stops)
            self._tree.insert('', 'end', iid=route.id,
                values=(stops_str,
                        f'{route.distance_km:,.0f}km', route.num_legs, n_ac,
                        f'{route.weekly_pax:,}', f'${route.ticket_price:.0f}',
                        rev_str, status),
                tags=(tag,))
        self._tree.tag_configure('active', foreground=GREEN)
        self._tree.tag_configure('idle', foreground=TEXT2)
        for iid in sel:
            if self._tree.exists(iid):
                self._tree.selection_set(iid)
        self._refresh_ac_list()

    def _on_route_select(self, event):
        self._refresh_ac_list()

    def _refresh_ac_list(self):
        for item in self._ac_tree.get_children():
            self._ac_tree.delete(item)
        sel = self._tree.selection()
        if not sel:
            return
        route = self.state.get_route(sel[0])
        if not route:
            return
        for serial in route.aircraft_ids:
            owned = self.state.get_owned(serial)
            if not owned:
                continue
            cond = f'{owned.condition * 100:.0f}%'
            hours = f'{owned.hours_flown:,}h'
            active_flight = next(
                (f for f in self.state.active_flights if f.serial == serial), None)
            in_flight = active_flight is not None
            status = '✈ In Flight' if in_flight else '🅿 At Gate'
            tag = 'inflight' if in_flight else 'gate'
            rev_str = money_str(active_flight.revenue) if active_flight else '—'
            self._ac_tree.insert('', 'end',
                values=(owned.name, cond, hours, rev_str, status), tags=(tag,))
        self._ac_tree.tag_configure('inflight', foreground=ACCENT2)
        self._ac_tree.tag_configure('gate', foreground=TEXT2)

    def _open_route(self):
        stops = [sv.get().strip().upper() for sv in self._stop_vars]
        stops = [s for s in stops if s]
        if len(stops) < 2:
            messagebox.showwarning('Missing Fields',
                                   'Select at least an origin and destination.', parent=self)
            return
        ok, msg = self.engine.open_route(stops)
        if ok:
            if self.on_map_refresh:
                self.on_map_refresh()
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()
            self._stop_vars = [tk.StringVar(), tk.StringVar()]
            self._render_stops()
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

        # Price entry dialog — withdraw/deiconify to avoid zero-height window on Wayland
        result = [None]
        dlg = tk.Toplevel(self)
        dlg.withdraw()
        dlg.title('Ticket Price')
        dlg.configure(bg=BG2)
        dlg.transient(self.winfo_toplevel())

        stops_str = '→'.join(route.stops)
        tk.Label(dlg,
            text=f'Set ticket price for {stops_str}\n'
                 f'Current: ${route.ticket_price:.0f}  ·  Total distance: {route.distance_km:.0f} km'
                 f'  ({route.num_legs} leg{"s" if route.num_legs > 1 else ""})\n'
                 f'Price is scaled per leg by distance. Lower prices attract more passengers.',
            fg=TEXT, bg=BG2, font=F_SMALL, justify='left').pack(padx=12, pady=(10, 6))

        entry_var = tk.StringVar(value=str(int(route.ticket_price)))
        entry = tk.Entry(dlg, textvariable=entry_var, bg=BG3, fg=TEXT,
                         insertbackground=TEXT, font=F_SMALL, width=10)
        entry.pack(padx=12, pady=4)
        entry.select_range(0, 'end')

        def on_set():
            try:
                val = float(entry_var.get())
                if 10 <= val <= 10000:
                    result[0] = val
                    dlg.destroy()
                else:
                    messagebox.showwarning('Invalid', 'Price must be between $10 and $10,000.', parent=dlg)
            except ValueError:
                messagebox.showwarning('Invalid', 'Enter a numeric price.', parent=dlg)

        entry.bind('<Return>', lambda e: on_set())
        btn_row = tk.Frame(dlg, bg=BG2)
        btn_row.pack(pady=8)
        icon_btn(btn_row, 'Set Price', on_set, color=ACCENT, font=F_SMALL).pack(side='left', padx=4)
        icon_btn(btn_row, 'Cancel', dlg.destroy, color='#3a3a3a', font=F_SMALL).pack(side='left', padx=4)

        dlg.update_idletasks()
        pw = self.winfo_toplevel()
        x = pw.winfo_rootx() + (pw.winfo_width() - dlg.winfo_reqwidth()) // 2
        y = pw.winfo_rooty() + (pw.winfo_height() - dlg.winfo_reqheight()) // 2
        dlg.geometry(f'{dlg.winfo_reqwidth()}x{dlg.winfo_reqheight()}+{x}+{y}')
        dlg.resizable(False, False)
        dlg.deiconify()
        dlg.grab_set()
        entry.focus_set()

        dlg.wait_window()

        if result[0] is not None:
            route.ticket_price = result[0]
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
        self._chart.bind('<Configure>', lambda e: self._draw_chart())

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
        w = c.winfo_width() if c.winfo_width() > 1 else 600
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

# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH PANEL
# ─────────────────────────────────────────────────────────────────────────────
class ResearchPanel(tk.Frame):
    def __init__(self, parent, state, engine: GameEngine, refresh_cb=None, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self.state = state
        self.engine = engine
        self.refresh_cb = refresh_cb
        self._selected_proj_id = None
        self._build()

    def _build(self):
        tk.Label(self, text='RESEARCH & INNOVATION', fg=GOLD, bg=BG2,
                 font=F_SUBHEAD).pack(anchor='w', padx=12, pady=(10, 2))

        # Active research progress bar
        self._progress_frame = tk.Frame(self, bg=BG3)
        self._progress_frame.pack(fill='x', padx=8, pady=4)
        self._progress_lbl = tk.Label(self._progress_frame, text='No active research',
                                       fg=TEXT2, bg=BG3, font=F_SMALL)
        self._progress_lbl.pack(anchor='w', padx=10, pady=(6, 2))
        self._progress_bar = tk.Canvas(self._progress_frame, bg=BG3,
                                        height=14, highlightthickness=0)
        self._progress_bar.pack(fill='x', padx=10, pady=(0, 6))

        # Main content: list + detail
        content = tk.Frame(self, bg=BG2)
        content.pack(fill='both', expand=True, padx=8, pady=4)

        # Left: project list
        list_frame = tk.Frame(content, bg=BG2)
        list_frame.pack(side='left', fill='both', expand=True)

        tk.Label(list_frame, text='AVAILABLE PROJECTS', fg=GOLD, bg=BG2,
                 font=F_SMALL).pack(anchor='w', padx=4, pady=(0, 2))

        cols = ('status', 'name', 'cost', 'duration', 'era')
        self._proj_tree = ttk.Treeview(list_frame, columns=cols, show='headings',
                                        selectmode='browse', style='Treeview')
        hdrs = [('status', '', 30), ('name', 'Project', 210),
                ('cost', 'Cost', 80), ('duration', 'Duration', 80), ('era', 'Era', 60)]
        for col, hdr, w in hdrs:
            self._proj_tree.heading(col, text=hdr)
            self._proj_tree.column(col, width=w, anchor='center')
        self._proj_tree.column('name', anchor='w')
        self._proj_tree.bind('<<TreeviewSelect>>', self._on_proj_select)

        sb = ttk.Scrollbar(list_frame, orient='vertical', command=self._proj_tree.yview)
        self._proj_tree.configure(yscrollcommand=sb.set)
        self._proj_tree.pack(side='left', fill='both', expand=True, pady=2)
        sb.pack(side='left', fill='y', pady=2)

        # Right: detail card
        detail_frame = tk.Frame(content, bg=BG3, width=260)
        detail_frame.pack(side='right', fill='y', padx=(8, 0))
        detail_frame.pack_propagate(False)

        self._detail_lbl = tk.Label(detail_frame,
                                     text='Select a project\nto view details',
                                     fg=TEXT2, bg=BG3, font=F_SMALL,
                                     justify='left', wraplength=240)
        self._detail_lbl.pack(padx=10, pady=10, anchor='nw')

        btn_area = tk.Frame(detail_frame, bg=BG3)
        btn_area.pack(fill='x', padx=10, pady=4, side='bottom')

        self._start_btn = icon_btn(btn_area, '🔬  Start Research', self._start_research,
                                    color=ACCENT, font=F_SMALL)
        self._start_btn.pack(fill='x', pady=2)
        self._start_btn.config(state='disabled')

        self._cancel_btn = icon_btn(btn_area, '✖  Cancel Research', self._cancel_research,
                                     color='#5a1a1a', font=F_SMALL)
        self._cancel_btn.pack(fill='x', pady=2)
        self._cancel_btn.config(state='disabled')

        self.refresh()

    def refresh(self):
        s = self.state
        self._populate_projects()
        self._update_progress()

    def _populate_projects(self):
        sel = self._proj_tree.selection()
        for item in self._proj_tree.get_children():
            self._proj_tree.delete(item)

        for proj in RESEARCH_PROJECTS:
            completed = proj.id in self.state.completed_research
            active = proj.id == self.state.active_research
            era_ok = proj.era_min <= self.state.year
            prereq_ok = (not proj.prerequisite or
                         proj.prerequisite in self.state.completed_research)

            if completed:
                status_icon = '✓'
                tag = 'done'
            elif active:
                status_icon = '▶'
                tag = 'active'
            elif not era_ok or not prereq_ok:
                status_icon = '🔒'
                tag = 'locked'
            else:
                status_icon = '○'
                tag = 'avail'

            cost_str = f'${proj.cost_m:.0f}M'
            dur_str = f'{proj.duration_days}d'
            era_str = str(proj.era_min)

            self._proj_tree.insert('', 'end', iid=proj.id,
                values=(status_icon, proj.name, cost_str, dur_str, era_str),
                tags=(tag,))

        self._proj_tree.tag_configure('done',   foreground=MUTED)
        self._proj_tree.tag_configure('active', foreground=ACCENT2)
        self._proj_tree.tag_configure('locked', foreground=MUTED)
        self._proj_tree.tag_configure('avail',  foreground=TEXT)

        for iid in sel:
            if self._proj_tree.exists(iid):
                self._proj_tree.selection_set(iid)

    def _update_progress(self):
        s = self.state
        bar = self._progress_bar
        bar.delete('all')

        if not s.active_research:
            self._progress_lbl.config(text='No active research  —  select a project and click Start',
                                       fg=TEXT2)
            self._cancel_btn.config(state='disabled')
            return

        proj = next((p for p in RESEARCH_PROJECTS if p.id == s.active_research), None)
        if not proj:
            return

        pct = min(1.0, s.research_progress_days / max(1, proj.duration_days))
        days_left = max(0, proj.duration_days - s.research_progress_days)
        self._progress_lbl.config(
            text=f'▶  {proj.name}  —  {pct*100:.0f}%  ({days_left:.0f} days remaining)',
            fg=ACCENT2)
        self._cancel_btn.config(state='normal')

        # Draw progress bar
        bar.update_idletasks()
        w = bar.winfo_width() or 400
        fill_w = int(w * pct)
        bar.create_rectangle(0, 0, w, 14, fill=BG3, outline='')
        if fill_w > 0:
            bar.create_rectangle(0, 0, fill_w, 14, fill=ACCENT, outline='')
        bar.create_text(w // 2, 7, text=f'{pct*100:.0f}%',
                        fill=WHITE, font=F_SMALL)

    def _on_proj_select(self, event):
        sel = self._proj_tree.selection()
        if not sel:
            return
        proj_id = sel[0]
        self._selected_proj_id = proj_id
        proj = next((p for p in RESEARCH_PROJECTS if p.id == proj_id), None)
        if not proj:
            return

        s = self.state
        completed = proj_id in s.completed_research
        active = proj_id == s.active_research
        era_ok = proj.era_min <= s.year
        prereq_ok = not proj.prerequisite or proj.prerequisite in s.completed_research
        cost = int(proj.cost_m * 1_000_000)
        affordable = cost <= s.cash

        if completed:
            state_txt = '✅ Completed'
            state_col = GREEN
        elif active:
            pct = min(100.0, s.research_progress_days / max(1, proj.duration_days) * 100)
            state_txt = f'▶ In Progress ({pct:.0f}%)'
            state_col = ACCENT2
        elif not era_ok:
            state_txt = f'🔒 Available from {proj.era_min}'
            state_col = MUTED
        elif not prereq_ok:
            prereq = next((p for p in RESEARCH_PROJECTS if p.id == proj.prerequisite), None)
            state_txt = f'🔒 Requires: {prereq.name if prereq else proj.prerequisite}'
            state_col = MUTED
        elif not affordable:
            state_txt = f'💸 Insufficient funds (need ${cost:,})'
            state_col = RED
        else:
            state_txt = '○ Available'
            state_col = TEXT

        sep = '─' * 30
        prereq_line = ''
        if proj.prerequisite:
            prereq = next((p for p in RESEARCH_PROJECTS if p.id == proj.prerequisite), None)
            prereq_status = '✓' if proj.prerequisite in s.completed_research else '✗'
            prereq_line = f'\nRequires: {prereq.name if prereq else proj.prerequisite} {prereq_status}'

        detail = (
            f'🔬 {proj.name}\n'
            f'{sep}\n\n'
            f'{proj.description}\n\n'
            f'💰  Cost: ${proj.cost_m:.0f}M\n'
            f'⏱  Duration: {proj.duration_days} days\n'
            f'📅  Available: {proj.era_min}+\n'
            f'{prereq_line}\n'
            f'{sep}\n'
            f'📈  Effect:\n{proj.effect_desc}\n\n'
            f'Status: {state_txt}'
        )
        self._detail_lbl.config(text=detail, fg=state_col if completed or not era_ok else TEXT)

        can_start = (not completed and not active and era_ok and
                     prereq_ok and affordable and not s.active_research)
        self._start_btn.config(state='normal' if can_start else 'disabled')

    def _start_research(self):
        if not self._selected_proj_id:
            return
        ok, msg = self.engine.start_research(self._selected_proj_id)
        if ok:
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()
        else:
            messagebox.showerror('Cannot Start Research', msg, parent=self)

    def _cancel_research(self):
        if not messagebox.askyesno(
                'Cancel Research',
                'Cancel current research?\n50% of the cost will be refunded.',
                parent=self):
            return
        ok, msg = self.engine.cancel_research()
        if ok:
            messagebox.showinfo('Research Cancelled', msg, parent=self)
            if self.refresh_cb:
                self.refresh_cb()
            self.refresh()


_SANS = 'Helvetica'
