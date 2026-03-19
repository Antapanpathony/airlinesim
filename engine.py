"""Game engine / state for Airline Empire"""
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from data import Aircraft, City, CITY_DICT, great_circle_km, get_aircraft, available_aircraft

# ── Historical events that trigger in specific years ──────────────────────────
HISTORICAL_EVENTS = [
    (1914, "World War I begins. Passenger flights severely limited.",        -0.3,  -50),
    (1918, "WWI ends. Surplus military aircraft flood the market.",           0.2,   20),
    (1929, "Wall Street Crash. Passenger numbers plummet.",                  -0.4, -100),
    (1933, "New Deal boosts US aviation infrastructure.",                     0.2,   30),
    (1939, "World War II erupts. International routes suspended.",           -0.5,  -80),
    (1945, "WWII ends. Pent-up travel demand explodes.",                      0.5,  100),
    (1952, "de Havilland Comet enters service — the jet age begins!",         0.3,   50),
    (1958, "Boeing 707 transforms transatlantic travel forever.",             0.4,   80),
    (1969, "Boeing 747 'Jumbo Jet' revolutionises mass air travel.",          0.5,  120),
    (1973, "Oil Crisis: fuel costs triple. Airlines struggle.",              -0.4, -150),
    (1976, "Concorde enters service — supersonic travel for the elite.",      0.2,   40),
    (1978, "US Airline Deregulation Act. New competition surges.",            0.3,   60),
    (1979, "Second oil shock. Fuel costs spike again.",                      -0.3, -100),
    (1991, "Gulf War. Air travel drops sharply.",                            -0.3,  -80),
    (2001, "9/11 attacks. Security costs soar, passenger confidence crashes.",-0.6, -200),
    (2003, "SARS epidemic. Asia-Pacific routes devastated.",                 -0.3, -100),
    (2008, "Global Financial Crisis. Business travel collapses.",            -0.35,-120),
    (2010, "Eyjafjallajökull eruption closes European airspace.",            -0.15, -40),
    (2020, "COVID-19 pandemic. Global aviation enters freefall.",            -0.8, -400),
    (2022, "Aviation recovery — pent-up demand returns stronger than ever.", 0.5,  150),
    (2029, "Boom Overture enters service — supersonic returns!",              0.3,   80),
    (2035, "Hydrogen-powered airliners certified — green era begins.",        0.4,  100),
    (2050, "Suborbital point-to-point flights become commercially viable.",   0.5,  200),
]

_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']


@dataclass
class OwnedAircraft:
    ac_id: str
    name: str
    serial: int          # unique number
    year_acquired: int
    hours_flown: int = 0
    condition: float = 1.0   # 0-1
    assigned_route: Optional[str] = None  # route id or None


@dataclass
class ActiveFlight:
    serial: int           # aircraft serial number
    route_id: str
    depart_day: float     # game_day when departed
    arrive_day: float     # game_day when it lands
    revenue_m: float      # revenue (millions) earned on arrival
    going: bool = True    # True = origin→dest, False = dest→origin


@dataclass
class Route:
    id: str
    origin: str      # city code
    dest: str        # city code
    distance_km: float
    ticket_price: float
    aircraft_ids: List[int] = field(default_factory=list)  # serial numbers
    active: bool = True
    weekly_pax: int = 0     # for display


@dataclass
class FinancialRecord:
    year: int
    month: int           # 1-12
    revenue: float
    costs: float
    profit: float
    cash_end: float


@dataclass
class GameState:
    airline_name: str = 'My Airline'
    hub_code: str = 'JFK'
    start_year: int = 1950
    year: int = 1950
    month: int = 1           # 1-12
    day: int = 1             # 1-31
    game_day: float = 0.0    # days elapsed since Jan 1 of start_year
    cash: float = 10.0       # millions USD
    reputation: float = 50.0 # 0-100
    total_pax: int = 0
    fleet: List[OwnedAircraft] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    active_flights: List[ActiveFlight] = field(default_factory=list)
    finance_history: List[FinancialRecord] = field(default_factory=list)
    events_log: List[str] = field(default_factory=list)
    unlocked_aircraft: List[str] = field(default_factory=list)
    _serial_counter: int = 1
    _triggered_events: List[int] = field(default_factory=list)

    # Running totals
    total_revenue: float = 0.0
    total_costs: float = 0.0

    # Current-period accumulators (reset each month)
    _period_revenue: float = 0.0
    _period_costs: float = 0.0

    def _update_date(self):
        """Recompute year/month/day from game_day."""
        years_elapsed = int(self.game_day / 365.25)
        self.year = self.start_year + years_elapsed
        doy = self.game_day - years_elapsed * 365.25  # 0-based day within year
        acc = 0
        for m_idx, mdays in enumerate(_MONTH_DAYS):
            if doy < acc + mdays:
                self.month = m_idx + 1
                self.day = max(1, int(doy - acc) + 1)
                return
            acc += mdays
        self.month = 12
        self.day = 31

    def date_str(self) -> str:
        return f'{_MONTH_NAMES[self.month - 1]} {self.day:02d}, {self.year}'

    def next_serial(self) -> int:
        s = self._serial_counter
        self._serial_counter += 1
        return s

    def get_route(self, rid: str) -> Optional[Route]:
        for r in self.routes:
            if r.id == rid:
                return r
        return None

    def get_owned(self, serial: int) -> Optional[OwnedAircraft]:
        for o in self.fleet:
            if o.serial == serial:
                return o
        return None

    def fleet_value(self) -> float:
        total = 0.0
        for o in self.fleet:
            ac = get_aircraft(o.ac_id)
            if ac:
                age_factor = max(0.2, 1.0 - (self.year - o.year_acquired) * 0.04)
                total += ac.cost_m * age_factor * o.condition
        return total

    @property
    def net_worth(self) -> float:
        return self.cash + self.fleet_value()


class GameEngine:
    def __init__(self, state: GameState):
        self.state = state

    # ── Aircraft purchasing ──────────────────────────────────────────────────

    def can_buy(self, ac: Aircraft) -> Tuple[bool, str]:
        if ac.year > self.state.year:
            return False, f"Not available until {ac.year}"
        if ac.cost_m > self.state.cash:
            return False, f"Need ${ac.cost_m:.1f}M (have ${self.state.cash:.1f}M)"
        return True, "OK"

    def buy_aircraft(self, ac: Aircraft) -> Tuple[bool, str]:
        ok, msg = self.can_buy(ac)
        if not ok:
            return False, msg
        self.state.cash -= ac.cost_m
        owned = OwnedAircraft(
            ac_id=ac.id,
            name=ac.name,
            serial=self.state.next_serial(),
            year_acquired=self.state.year,
        )
        self.state.fleet.append(owned)
        self.state.events_log.append(
            f"{self.state.date_str()}: Purchased {ac.name} for ${ac.cost_m:.1f}M"
        )
        return True, f"Purchased {ac.name}"

    def sell_aircraft(self, serial: int) -> Tuple[bool, str]:
        owned = self.state.get_owned(serial)
        if not owned:
            return False, "Aircraft not found"
        if owned.assigned_route:
            return False, "Remove from route first"
        ac = get_aircraft(owned.ac_id)
        if not ac:
            return False, "Unknown aircraft type"
        age = self.state.year - owned.year_acquired
        sale_price = ac.cost_m * max(0.15, 1.0 - age * 0.04) * owned.condition
        self.state.cash += sale_price
        self.state.active_flights = [
            f for f in self.state.active_flights if f.serial != serial
        ]
        self.state.fleet.remove(owned)
        self.state.events_log.append(
            f"{self.state.date_str()}: Sold {owned.name} for ${sale_price:.2f}M"
        )
        return True, f"Sold {owned.name} for ${sale_price:.2f}M"

    # ── Routes ───────────────────────────────────────────────────────────────

    def open_route(self, origin: str, dest: str) -> Tuple[bool, str]:
        if origin == dest:
            return False, "Origin and destination must differ"
        rid = f"{min(origin,dest)}-{max(origin,dest)}"
        if any(r.id == rid for r in self.state.routes):
            return False, "Route already exists"
        c1 = CITY_DICT.get(origin)
        c2 = CITY_DICT.get(dest)
        if not c1 or not c2:
            return False, "Unknown city"
        dist = great_circle_km(c1.lat, c1.lon, c2.lat, c2.lon)
        ticket = self._base_ticket(dist)
        route = Route(id=rid, origin=origin, dest=dest,
                      distance_km=dist, ticket_price=ticket)
        self.state.routes.append(route)
        self.state.events_log.append(
            f"{self.state.date_str()}: Opened route {origin}→{dest} ({dist:.0f} km)"
        )
        return True, f"Opened {origin}–{dest}"

    def close_route(self, rid: str) -> Tuple[bool, str]:
        route = self.state.get_route(rid)
        if not route:
            return False, "Route not found"
        for serial in list(route.aircraft_ids):
            owned = self.state.get_owned(serial)
            if owned:
                owned.assigned_route = None
        self.state.active_flights = [
            f for f in self.state.active_flights if f.route_id != rid
        ]
        self.state.routes.remove(route)
        return True, f"Closed route {rid}"

    def assign_aircraft(self, serial: int, rid: str) -> Tuple[bool, str]:
        owned = self.state.get_owned(serial)
        if not owned:
            return False, "Aircraft not found"
        route = self.state.get_route(rid)
        if not route:
            return False, "Route not found"
        ac = get_aircraft(owned.ac_id)
        if ac and route.distance_km > ac.range_km and ac.range_km > 0:
            return False, f"{ac.name} range ({ac.range_km} km) < route distance ({route.distance_km:.0f} km)"
        if owned.assigned_route:
            old = self.state.get_route(owned.assigned_route)
            if old and serial in old.aircraft_ids:
                old.aircraft_ids.remove(serial)
            self.state.active_flights = [
                f for f in self.state.active_flights if f.serial != serial
            ]
        owned.assigned_route = rid
        if serial not in route.aircraft_ids:
            route.aircraft_ids.append(serial)
        return True, f"Assigned {owned.name} to {rid}"

    def unassign_aircraft(self, serial: int) -> Tuple[bool, str]:
        owned = self.state.get_owned(serial)
        if not owned:
            return False, "Aircraft not found"
        if not owned.assigned_route:
            return False, "Not assigned to any route"
        route = self.state.get_route(owned.assigned_route)
        if route and serial in route.aircraft_ids:
            route.aircraft_ids.remove(serial)
        self.state.active_flights = [
            f for f in self.state.active_flights if f.serial != serial
        ]
        owned.assigned_route = None
        return True, "Unassigned"

    # ── Economics ─────────────────────────────────────────────────────────────

    def _base_ticket(self, dist_km: float) -> float:
        base = 0.12 * dist_km
        return max(50, min(base, 2500))

    def _route_demand(self, route: Route) -> int:
        """Estimated passengers per flight (one-way)."""
        c1 = CITY_DICT.get(route.origin)
        c2 = CITY_DICT.get(route.dest)
        if not c1 or not c2:
            return 0
        pop_factor = math.sqrt(c1.population_m * c2.population_m)
        dist_factor = max(0.3, 1.0 - route.distance_km / 20000)
        hub_bonus = 1.5 if (c1.hub_tier == 1 or c2.hub_tier == 1) else 1.0
        rep_factor = 0.5 + self.state.reputation / 100
        base = pop_factor * dist_factor * hub_bonus * rep_factor * 60
        return int(base * random.uniform(0.85, 1.15))

    def _schedule_flight(self, owned: OwnedAircraft, route: Route,
                         going: bool = True):
        """Schedule the next one-way flight for this aircraft."""
        s = self.state
        ac = get_aircraft(owned.ac_id)
        if not ac or not route:
            return
        # Realistic flight duration: distance ÷ speed (hours) + 0.5h turnaround
        flight_hours = route.distance_km / max(1, ac.speed_kmh) + 0.5
        flight_days = flight_hours / 24.0

        depart_day = s.game_day
        arrive_day = depart_day + flight_days

        demand = self._route_demand(route)
        pax = min(ac.passengers, demand)
        load_factor = pax / max(1, ac.passengers)
        yield_adj = 0.8 + load_factor * 0.4
        revenue_m = pax * route.ticket_price * yield_adj / 1_000_000

        s.active_flights.append(ActiveFlight(
            serial=owned.serial,
            route_id=route.id,
            depart_day=depart_day,
            arrive_day=arrive_day,
            revenue_m=revenue_m,
            going=going,
        ))

    # ── Real-time tick ─────────────────────────────────────────────────────────

    def tick(self, delta_hours: float) -> Dict:
        """Advance game time by delta_hours. Called at ~20 FPS by the UI."""
        s = self.state
        old_year = s.year
        old_month = s.month

        s.game_day += delta_hours / 24.0
        s._update_date()

        events_triggered = []
        revenue = 0.0
        costs = 0.0
        pax_total = 0

        # Process arrived flights
        arrived = [f for f in s.active_flights if s.game_day >= f.arrive_day]
        for flight in arrived:
            s.active_flights.remove(flight)
            s.cash += flight.revenue_m
            revenue += flight.revenue_m
            s.total_revenue += flight.revenue_m
            s._period_revenue += flight.revenue_m

            owned = s.get_owned(flight.serial)
            route = s.get_route(flight.route_id)
            if owned and route:
                ac = get_aircraft(owned.ac_id)
                if ac:
                    demand = self._route_demand(route)
                    pax = min(ac.passengers, demand)
                    s.total_pax += pax
                    pax_total += pax
                    owned.condition = max(
                        0.3, owned.condition - random.uniform(0.0005, 0.002)
                    )
                    owned.hours_flown += int(
                        (flight.arrive_day - flight.depart_day) * 24
                    )
                    # Update weekly_pax estimate on the route
                    days_per_flight = max(0.001, flight.arrive_day - flight.depart_day)
                    route.weekly_pax = int(pax * 7.0 / days_per_flight)

        # Schedule new flights for idle aircraft on active routes
        for owned in s.fleet:
            if owned.assigned_route:
                in_flight = any(f.serial == owned.serial for f in s.active_flights)
                if not in_flight:
                    route = s.get_route(owned.assigned_route)
                    if route:
                        # Alternate direction for realism
                        last = next(
                            (f for f in reversed(s.active_flights)
                             if f.serial == owned.serial), None
                        )
                        going = not last.going if last else True
                        self._schedule_flight(owned, route, going=going)

        # Daily operating costs (accrued proportionally to delta)
        delta_days = delta_hours / 24.0
        for owned in s.fleet:
            ac = get_aircraft(owned.ac_id)
            if ac:
                daily_m = ac.monthly_cost_k / 30.0 / 1000.0
                if not owned.assigned_route:
                    daily_m *= 0.4  # parked aircraft cost less
                c = daily_m * delta_days
                costs += c
                s.cash -= c
                s.total_costs += c
                s._period_costs += c

        # Fixed overhead
        overhead_daily = max(0.0002,
                             (len(s.fleet) * 0.02 + len(s.routes) * 0.01) / 90.0)
        ov = overhead_daily * delta_days
        costs += ov
        s.cash -= ov
        s.total_costs += ov
        s._period_costs += ov

        # Reputation drift
        if pax_total > 0:
            s.reputation = min(100.0, s.reputation + 0.02 * delta_days)
        else:
            s.reputation = max(0.0, s.reputation - 0.05 * delta_days)

        # Monthly financial snapshot at month boundary
        if s.month != old_month or s.year != old_year:
            rec = FinancialRecord(
                old_year, old_month,
                s._period_revenue, s._period_costs,
                s._period_revenue - s._period_costs,
                s.cash,
            )
            s.finance_history.append(rec)
            s._period_revenue = 0.0
            s._period_costs = 0.0

        # Historical events at year change
        if s.year != old_year:
            for yr, desc, demand_mult, cash_effect in HISTORICAL_EVENTS:
                if yr == s.year and yr not in s._triggered_events:
                    s._triggered_events.append(yr)
                    rep_change = demand_mult * 20
                    s.reputation = max(0.0, min(100.0, s.reputation + rep_change))
                    s.cash += cash_effect / 1000.0  # apply cash impact
                    s.events_log.append(f"📰 {s.year}: {desc}")
                    events_triggered.append(desc)

        return {
            'revenue': revenue,
            'costs': costs,
            'pax': pax_total,
            'events': events_triggered,
            'cash': s.cash,
        }


def new_game(name: str, hub: str, start_year: int, difficulty: str) -> GameState:
    budgets = {'easy': 25.0, 'normal': 10.0, 'hard': 5.0, 'tycoon': 2.0}
    cash = budgets.get(difficulty, 10.0)
    s = GameState(
        airline_name=name,
        hub_code=hub,
        start_year=start_year,
        year=start_year,
        month=1,
        day=1,
        game_day=0.0,
        cash=cash,
        reputation=40.0,
    )
    # Starting aircraft gift based on era
    starters = {
        range(1900, 1920): 'benoist',
        range(1920, 1935): 'ford5at',
        range(1935, 1950): 'dc3',
        range(1950, 1960): 'dc6',
        range(1960, 1970): 'b707',
        range(1970, 1985): 'b737_100',
        range(1985, 2000): 'a320',
        range(2000, 2015): 'b737ng',
        range(2015, 2030): 'a320neo',
        range(2030, 2051): 'boeing_nma',
    }
    starter_id = 'dc3'
    for yr_range, ac_id in starters.items():
        if start_year in yr_range:
            starter_id = ac_id
            break

    ac = get_aircraft(starter_id)
    if ac:
        owned = OwnedAircraft(
            ac_id=starter_id,
            name=ac.name,
            serial=s.next_serial(),
            year_acquired=start_year,
        )
        s.fleet.append(owned)

    s.events_log.append(f"🛫 {name} founded in {start_year} with hub at {hub}. Good luck!")
    return s
