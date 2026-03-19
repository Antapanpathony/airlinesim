"""Interactive world map canvas widget"""
import tkinter as tk
import math
from typing import Optional, Callable, List, Tuple
from ui_theme import *
from data import CITIES, CITY_DICT, City

# Simplified continent outlines as (lat, lon) lists
# Equirectangular projection: x=(lon+180)/360*W, y=(90-lat)/180*H
CONTINENTS = {
    'north_america': [
        (71,-141),(70,-130),(60,-140),(58,-137),(54,-133),(50,-128),(47,-124),
        (38,-122),(34,-120),(29,-115),(23,-110),(15,-92),(8,-77),(9,-79),
        (15,-83),(16,-90),(21,-87),(25,-80),(35,-76),(41,-70),(45,-66),
        (47,-53),(52,-56),(58,-56),(62,-64),(68,-65),(70,-60),(73,-83),
        (73,-95),(70,-105),(72,-120),(72,-141),
    ],
    'south_america': [
        (11,-73),(10,-62),(8,-60),(5,-52),(1,-50),(0,-50),(-5,-35),
        (-10,-37),(-15,-39),(-22,-42),(-26,-48),(-33,-53),(-34,-58),
        (-41,-62),(-50,-68),(-54,-68),(-55,-66),(-50,-75),(-45,-73),
        (-40,-73),(-33,-71),(-20,-70),(-5,-81),(0,-80),(5,-77),(11,-73),
    ],
    'europe': [
        (71,28),(70,18),(65,14),(58,5),(51,2),(44,-2),(36,-6),(36,0),
        (37,6),(43,7),(44,8),(44,15),(41,12),(41,16),(43,28),(41,29),
        (37,23),(36,30),(40,36),(47,40),(43,41),(42,45),(47,38),(52,38),
        (55,37),(57,24),(60,22),(60,25),(65,25),(70,28),(71,28),
    ],
    'africa': [
        (37,10),(36,3),(34,-5),(32,-9),(28,-13),(15,-17),(5,-15),(4,-8),
        (4,2),(2,9),(5,1),(0,9),(-5,12),(-10,16),(-15,12),(-20,35),
        (-26,34),(-34,18),(-34,26),(-26,33),(-20,44),(-12,44),(-5,40),
        (5,42),(11,45),(12,51),(15,42),(22,37),(30,32),(37,40),(37,30),(37,10),
    ],
    'asia': [
        (71,28),(71,60),(73,100),(73,140),(68,180),(60,162),(52,143),
        (45,138),(43,131),(38,121),(24,118),(22,114),(10,104),(1,104),
        (1,103),(3,98),(7,77),(8,77),(13,80),(22,68),(24,62),(27,56),
        (23,57),(12,45),(10,43),(12,51),(15,50),(22,58),(37,55),(37,40),
        (42,44),(47,40),(40,36),(42,45),(52,38),(55,37),(57,24),(60,22),
        (65,25),(70,28),(71,28),
    ],
    'australia': [
        (-14,126),(-12,136),(-12,136),(-11,136),(-12,142),(-18,148),
        (-25,152),(-33,152),(-38,148),(-39,145),(-38,140),(-35,137),
        (-33,134),(-32,115),(-22,113),(-14,126),
    ],
    'greenland': [
        (76,-73),(71,-53),(60,-44),(61,-45),(66,-54),(68,-50),(73,-36),
        (83,-36),(83,-60),(76,-73),
    ],
    'new_zealand': [
        (-34,172),(-46,169),(-46,168),(-43,171),(-34,172),
    ],
    'japan': [
        (33,130),(35,136),(37,137),(38,141),(40,140),(45,141),(45,142),
        (43,144),(42,143),(35,136),(34,130),(33,130),
    ],
    'uk_ireland': [
        (49,-6),(51,-1),(58,0),(60,-1),(58,-5),(51,-5),(51,-3),(50,-5),(49,-6),
    ],
    'iceland': [
        (63,-24),(64,-14),(65,-13),(66,-14),(66,-18),(64,-24),(63,-24),
    ],
}

class WorldMap(tk.Canvas):
    """Zoomable, pannable world map with cities and routes."""

    def __init__(self, parent, game_state=None, on_city_click: Optional[Callable] = None, **kw):
        super().__init__(parent, bg=OCEAN, highlightthickness=0, **kw)
        self.game_state = game_state
        self.on_city_click = on_city_click

        self._drag_start = None
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._zoom = 1.0
        self._anim_offset = 0  # for animated routes

        self._city_items = {}   # code -> canvas item id
        self._route_items = {}  # rid -> list of item ids
        self._hover_city: Optional[str] = None

        self.bind('<Configure>', self._on_resize)
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<MouseWheel>', self._on_scroll)
        self.bind('<Button-4>', lambda e: self._zoom_at(e.x, e.y, 1.12))
        self.bind('<Button-5>', lambda e: self._zoom_at(e.x, e.y, 0.88))
        self.bind('<Motion>', self._on_motion)

        self._anim_id = None
        self.after(100, self._start_anim)

    # ── coordinate transforms ─────────────────────────────────────────────────

    def _ll_to_base(self, lat: float, lon: float) -> Tuple[float, float]:
        """Lat/lon → base canvas coords (before pan/zoom)."""
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        x = (lon + 180) / 360 * w
        y = (90 - lat) / 180 * h
        return x, y

    def _apply_transform(self, bx: float, by: float) -> Tuple[float, float]:
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        cx, cy = w/2, h/2
        x = (bx - cx) * self._zoom + cx + self._pan_x
        y = (by - cy) * self._zoom + cy + self._pan_y
        return x, y

    def _ll_to_canvas(self, lat: float, lon: float) -> Tuple[float, float]:
        return self._apply_transform(*self._ll_to_base(lat, lon))

    def _canvas_to_ll(self, cx_: float, cy_: float) -> Tuple[float, float]:
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        cx, cy = w/2, h/2
        bx = (cx_ - cx - self._pan_x) / self._zoom + cx
        by = (cy_ - cy - self._pan_y) / self._zoom + cy
        lon = bx / w * 360 - 180
        lat = 90 - by / h * 180
        return lat, lon

    # ── drawing ───────────────────────────────────────────────────────────────

    def redraw(self):
        self.delete('all')
        self._city_items.clear()
        self._route_items.clear()
        self._draw_ocean()
        self._draw_continents()
        self._draw_grid()
        self._draw_routes()
        self._draw_cities()
        self._draw_flights()

    def _draw_ocean(self):
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        self.create_rectangle(0, 0, w, h, fill=OCEAN, outline='')
        # subtle gradient bands
        for i in range(8):
            y = i * h // 8
            alpha = i / 8 * 0.3
            shade = lerp_color(OCEAN, '#0a2540', alpha)
            self.create_rectangle(0, y, w, y + h//8, fill=shade, outline='')

    def _draw_grid(self):
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        # longitude lines every 30°
        for lon in range(-180, 181, 30):
            x1, y1 = self._ll_to_canvas(90, lon)
            x2, y2 = self._ll_to_canvas(-90, lon)
            self.create_line(x1, y1, x2, y2, fill='#0d2a45', width=1, dash=(2, 8))
        # latitude lines every 30°
        for lat in range(-60, 91, 30):
            x1, y1 = self._ll_to_canvas(lat, -180)
            x2, y2 = self._ll_to_canvas(lat, 180)
            self.create_line(x1, y1, x2, y2, fill='#0d2a45', width=1, dash=(2, 8))
        # Equator
        x1, y1 = self._ll_to_canvas(0, -180)
        x2, y2 = self._ll_to_canvas(0, 180)
        self.create_line(x1, y1, x2, y2, fill='#153550', width=1)

    def _draw_continents(self):
        for name, pts in CONTINENTS.items():
            canvas_pts = []
            for lat, lon in pts:
                x, y = self._ll_to_canvas(lat, lon)
                canvas_pts.extend([x, y])
            if len(canvas_pts) >= 6:
                self.create_polygon(canvas_pts, fill=LAND, outline=LAND2,
                                    width=1, smooth=True)

    def _great_circle_arc(self, lat1, lon1, lat2, lon2, steps=40) -> List[float]:
        """Return canvas coords list for a great-circle arc."""
        pts = []
        for i in range(steps + 1):
            t = i / steps
            # Slerp in 3D
            phi1, lam1 = math.radians(lat1), math.radians(lon1)
            phi2, lam2 = math.radians(lat2), math.radians(lon2)
            x1 = math.cos(phi1) * math.cos(lam1)
            y1 = math.cos(phi1) * math.sin(lam1)
            z1 = math.sin(phi1)
            x2 = math.cos(phi2) * math.cos(lam2)
            y2 = math.cos(phi2) * math.sin(lam2)
            z2 = math.sin(phi2)
            dot = min(1.0, max(-1.0, x1*x2 + y1*y2 + z1*z2))
            omega = math.acos(dot)
            if omega < 0.0001:
                xi, yi, zi = x1, y1, z1
            else:
                s = math.sin(omega)
                xi = (math.sin((1-t)*omega)*x1 + math.sin(t*omega)*x2) / s
                yi = (math.sin((1-t)*omega)*y1 + math.sin(t*omega)*y2) / s
                zi = (math.sin((1-t)*omega)*z1 + math.sin(t*omega)*z2) / s
            lat_i = math.degrees(math.asin(max(-1.0, min(1.0, zi))))
            lon_i = math.degrees(math.atan2(yi, xi))
            cx_, cy_ = self._ll_to_canvas(lat_i, lon_i)
            pts.extend([cx_, cy_])
        return pts

    def _draw_routes(self):
        if not self.game_state:
            return
        for route in self.game_state.routes:
            c1 = CITY_DICT.get(route.origin)
            c2 = CITY_DICT.get(route.dest)
            if not c1 or not c2:
                continue
            pts = self._great_circle_arc(c1.lat, c1.lon, c2.lat, c2.lon, steps=30)
            active = bool(route.aircraft_ids)
            color = ROUTE_A if active else ROUTE_C
            width = 2 if active else 1
            dash = None if active else (6, 4)

            items = []
            if pts and len(pts) >= 4:
                kw = dict(fill=color, width=width, smooth=True, joinstyle='round',
                          capstyle='round')
                if dash:
                    kw['dash'] = dash
                item = self.create_line(*pts, **kw)
                items.append(item)

                # Arrow mid-point
                mid = len(pts) // 2
                if mid + 2 < len(pts):
                    mx, my = pts[mid], pts[mid+1]
                    mx2, my2 = pts[mid+2], pts[mid+3]
                    angle = math.atan2(my2 - my, mx2 - mx)
                    sz = 7
                    arrow_pts = [
                        mx + sz*math.cos(angle), my + sz*math.sin(angle),
                        mx + sz*math.cos(angle+2.5), my + sz*math.sin(angle+2.5),
                        mx + sz*math.cos(angle-2.5), my + sz*math.sin(angle-2.5),
                    ]
                    a = self.create_polygon(arrow_pts, fill=color, outline='')
                    items.append(a)

            self._route_items[route.id] = items

    def _draw_cities(self):
        hub = self.game_state.hub_code if self.game_state else None
        # Collect cities used in routes for highlighting
        route_cities = set()
        if self.game_state:
            for r in self.game_state.routes:
                route_cities.add(r.origin)
                route_cities.add(r.dest)

        for city in CITIES:
            cx_, cy_ = self._ll_to_canvas(city.lat, city.lon)
            is_hub = city.code == hub
            is_route = city.code in route_cities
            is_hover = city.code == self._hover_city

            if is_hub:
                r = 7
                fill = GOLD
                outline = '#fff8e0'
                ow = 2
            elif is_route:
                r = 5
                fill = ACCENT2
                outline = WHITE
                ow = 1
            else:
                r = 3
                fill = TEXT2
                outline = MUTED
                ow = 1

            if is_hover:
                r += 2
                outline = WHITE
                ow = 2

            item = self.create_oval(cx_-r, cy_-r, cx_+r, cy_+r,
                                     fill=fill, outline=outline, width=ow,
                                     tags=('city', city.code))
            self._city_items[city.code] = item

            # Label for major cities or hovered/route cities
            if is_hub or is_hover or (is_route and city.hub_tier <= 2):
                font_size = 9 if city.hub_tier > 1 else 10
                lbl_y = cy_ - r - 7
                self.create_text(cx_, lbl_y, text=city.code,
                                  fill=GOLD if is_hub else (WHITE if is_hover else TEXT2),
                                  font=(_SANS if '_SANS' in dir() else 'Helvetica',
                                        font_size, 'bold' if is_hub else 'normal'),
                                  anchor='s', tags=('city_lbl', city.code))

        # Hub glow ring
        if hub and hub in self.game_state.hub_code if self.game_state else False:
            city = CITY_DICT.get(hub)
            if city:
                cx_, cy_ = self._ll_to_canvas(city.lat, city.lon)
                for ri, alpha in [(14, '#3a2800'), (11, '#5a3d00')]:
                    self.create_oval(cx_-ri, cy_-ri, cx_+ri, cy_+ri,
                                      fill='', outline=alpha, width=1)

    def _interpolate_gc(self, lat1, lon1, lat2, lon2, t):
        """Interpolate along a great-circle arc at fraction t (0=origin, 1=dest)."""
        phi1, lam1 = math.radians(lat1), math.radians(lon1)
        phi2, lam2 = math.radians(lat2), math.radians(lon2)
        x1 = math.cos(phi1) * math.cos(lam1)
        y1 = math.cos(phi1) * math.sin(lam1)
        z1 = math.sin(phi1)
        x2 = math.cos(phi2) * math.cos(lam2)
        y2 = math.cos(phi2) * math.sin(lam2)
        z2 = math.sin(phi2)
        dot = min(1.0, max(-1.0, x1*x2 + y1*y2 + z1*z2))
        omega = math.acos(dot)
        if omega < 0.0001:
            xi, yi, zi = x1, y1, z1
        else:
            s = math.sin(omega)
            xi = (math.sin((1-t)*omega)*x1 + math.sin(t*omega)*x2) / s
            yi = (math.sin((1-t)*omega)*y1 + math.sin(t*omega)*y2) / s
            zi = (math.sin((1-t)*omega)*z1 + math.sin(t*omega)*z2) / s
        lat_i = math.degrees(math.asin(max(-1.0, min(1.0, zi))))
        lon_i = math.degrees(math.atan2(yi, xi))
        return lat_i, lon_i

    def _draw_flights(self):
        """Draw active in-flight aircraft as gold dots moving along their routes."""
        if not self.game_state:
            return
        flights = getattr(self.game_state, 'active_flights', [])
        for flight in flights:
            route = self.game_state.get_route(flight.route_id)
            if not route:
                continue
            c1 = CITY_DICT.get(route.origin)
            c2 = CITY_DICT.get(route.dest)
            if not c1 or not c2:
                continue
            total = flight.arrive_day - flight.depart_day
            if total <= 0:
                continue
            progress = (self.game_state.game_day - flight.depart_day) / total
            progress = max(0.0, min(1.0, progress))
            # going=True: origin→dest; going=False: dest→origin
            if not flight.going:
                progress = 1.0 - progress
            lat, lon = self._interpolate_gc(c1.lat, c1.lon, c2.lat, c2.lon, progress)
            cx_, cy_ = self._ll_to_canvas(lat, lon)
            r = 4
            self.create_oval(cx_-r, cy_-r, cx_+r, cy_+r,
                             fill=GOLD, outline=WHITE, width=1,
                             tags=('flight',))

    # ── interaction ───────────────────────────────────────────────────────────

    def _on_resize(self, event):
        self.after_idle(self.redraw)

    def _on_press(self, event):
        self._drag_start = (event.x, event.y, self._pan_x, self._pan_y)
        self._click_pos = (event.x, event.y)

    def _on_drag(self, event):
        if self._drag_start:
            sx, sy, spx, spy = self._drag_start
            self._pan_x = spx + (event.x - sx)
            self._pan_y = spy + (event.y - sy)
            self.redraw()

    def _on_release(self, event):
        if self._drag_start:
            sx, sy = self._drag_start[0], self._drag_start[1]
            dist = math.hypot(event.x - sx, event.y - sy)
            if dist < 5:
                # It's a click, not a drag
                self._handle_click(event.x, event.y)
        self._drag_start = None

    def _handle_click(self, ex, ey):
        # Find nearest city within 15px
        best_city = None
        best_dist = 15
        for city in CITIES:
            cx_, cy_ = self._ll_to_canvas(city.lat, city.lon)
            d = math.hypot(ex - cx_, ey - cy_)
            if d < best_dist:
                best_dist = d
                best_city = city
        if best_city and self.on_city_click:
            self.on_city_click(best_city)

    def _on_motion(self, event):
        # Hover detection
        best_city = None
        best_dist = 15
        for city in CITIES:
            cx_, cy_ = self._ll_to_canvas(city.lat, city.lon)
            d = math.hypot(event.x - cx_, event.y - cy_)
            if d < best_dist:
                best_dist = d
                best_city = city
        new_hover = best_city.code if best_city else None
        if new_hover != self._hover_city:
            self._hover_city = new_hover
            self.redraw()
            if new_hover:
                self.config(cursor='hand2')
            else:
                self.config(cursor='')

    def _on_scroll(self, event):
        factor = 1.12 if event.delta > 0 else 0.88
        self._zoom_at(event.x, event.y, factor)

    def _zoom_at(self, mx, my, factor):
        w = self.winfo_width() or 1200
        h = self.winfo_height() or 600
        cx, cy = w/2, h/2
        # Adjust pan so zoom is centered on mouse
        self._pan_x = (self._pan_x - mx + cx) * factor + mx - cx
        self._pan_y = (self._pan_y - my + cy) * factor + my - cy
        self._zoom = max(0.5, min(8.0, self._zoom * factor))
        self.redraw()

    def reset_view(self):
        self._pan_x = 0
        self._pan_y = 0
        self._zoom = 1.0
        self.redraw()

    # ── animation ─────────────────────────────────────────────────────────────

    def _start_anim(self):
        self.redraw()
        self._anim_id = self.after(500, self._start_anim)

    def destroy(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
        super().destroy()

_SANS = 'Helvetica'
