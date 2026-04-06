"""Game engine / state for Airline Empire"""
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from data import Aircraft, City, CITY_DICT, great_circle_km, get_aircraft, available_aircraft

# ── Cabin class constants ──────────────────────────────────────────────────────
CABIN_MULTIPLIERS = {
    'economy':          1.0,
    'premium_economy':  1.6,
    'business':         3.5,
    'first':            7.0,
    'supersonic_first': 15.0,
}
# Fraction of total route demand that each class draws
CABIN_DEMAND_FRACTIONS = {
    'economy':          1.00,
    'premium_economy':  0.30,
    'business':         0.15,
    'first':            0.05,
    'supersonic_first': 0.02,
}
CABIN_DISPLAY_NAMES = {
    'economy':          'Economy',
    'premium_economy':  'Premium Economy',
    'business':         'Business Class',
    'first':            'First Class',
    'supersonic_first': 'Supersonic First',
}
# Physical space each seat class occupies relative to one economy seat.
# Upgrading to premium/business/first reduces total seat count.
CABIN_SEAT_SIZES = {
    'economy':          1.0,
    'premium_economy':  1.5,   # 100 eco → max 66 PE
    'business':         2.5,   # 100 eco → max 40 business
    'first':            4.0,   # 100 eco → max 25 first
    'supersonic_first': 5.0,
}

# ── Research projects ──────────────────────────────────────────────────────────
@dataclass
class ResearchProject:
    id: str
    name: str
    description: str
    cost_m: float        # cost in millions USD
    duration_days: int   # game days to complete
    era_min: int         # earliest year available
    effect_desc: str     # human-readable effect
    prerequisite: str = ''   # id of required completed research
    unlocks_cabin: str = ''  # cabin class this unlocks (if any)


RESEARCH_PROJECTS: List[ResearchProject] = [
    ResearchProject(
        id='premium_economy',
        name='Premium Economy Cabin',
        description='Introduce a comfortable premium economy section with extra legroom, better meals, and priority boarding.',
        cost_m=2.0, duration_days=90, era_min=1950,
        effect_desc='Unlocks Premium Economy seating (1.6× revenue per seat)',
        unlocks_cabin='premium_economy',
    ),
    ResearchProject(
        id='business_class',
        name='Business Class Service',
        description='Create a dedicated business class cabin with wider seats, lie-flat capability, and premium meal service.',
        cost_m=5.0, duration_days=180, era_min=1960,
        effect_desc='Unlocks Business Class seating (3.5× revenue per seat)',
        prerequisite='premium_economy',
        unlocks_cabin='business',
    ),
    ResearchProject(
        id='first_class',
        name='First Class Suites',
        description='Develop exclusive first class suites with private doors, gourmet dining, and luxury amenities.',
        cost_m=10.0, duration_days=270, era_min=1970,
        effect_desc='Unlocks First Class seating (7× revenue per seat)',
        prerequisite='business_class',
        unlocks_cabin='first',
    ),
    ResearchProject(
        id='fuel_efficiency',
        name='Fuel Efficiency Programme',
        description='Invest in fuel-saving procedures, winglet retrofits, and engine management optimisation.',
        cost_m=3.0, duration_days=120, era_min=1973,
        effect_desc='Reduces all aircraft operating costs by 20%',
    ),
    ResearchProject(
        id='budget_subsidiary',
        name='Budget Airline Subsidiary',
        description='Launch a low-cost carrier subsidiary to capture price-sensitive travellers. Streamlined operations, no-frills service.',
        cost_m=8.0, duration_days=180, era_min=1978,
        effect_desc='Reduces overhead costs by 30% and boosts economy demand by 20%',
    ),
    ResearchProject(
        id='frequent_flyer',
        name='Frequent Flyer Programme',
        description='Build a loyalty rewards scheme to retain passengers and increase repeat bookings across your network.',
        cost_m=4.0, duration_days=90, era_min=1981,
        effect_desc='Increases passenger demand on all routes by 15%',
    ),
    ResearchProject(
        id='advanced_materials',
        name='Advanced Composite Interiors',
        description='Retrofit fleet interiors with lightweight composite materials to cut maintenance costs and fuel burn.',
        cost_m=6.0, duration_days=150, era_min=1990,
        effect_desc='Reduces monthly aircraft maintenance costs by 15%',
    ),
    ResearchProject(
        id='premium_ife',
        name='Premium In-Flight Entertainment',
        description='Install state-of-the-art IFE systems with personal screens, Wi-Fi, and curated content to justify premium fares.',
        cost_m=5.0, duration_days=120, era_min=2000,
        effect_desc='Increases Business and First Class revenue by 25%',
        prerequisite='business_class',
    ),
    ResearchProject(
        id='sustainable_aviation',
        name='Sustainable Aviation Initiative',
        description='Transition to sustainable aviation fuel and green operations to attract eco-conscious travellers and cut long-term costs.',
        cost_m=12.0, duration_days=365, era_min=2020,
        effect_desc='Reduces operating costs for SAF and hydrogen aircraft by 30%',
    ),
    ResearchProject(
        id='supersonic_lounge',
        name='Supersonic Premium Lounge',
        description='Design an ultra-exclusive supersonic first class experience — private suites, Michelin-star dining, and unrivalled speed.',
        cost_m=20.0, duration_days=365, era_min=2025,
        effect_desc='Unlocks Supersonic First Class (15× revenue per seat) for supersonic aircraft',
        prerequisite='first_class',
        unlocks_cabin='supersonic_first',
    ),
]

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
    last_going: Optional[bool] = None    # direction of last completed flight
    cabin_config: Dict[str, int] = field(default_factory=dict)  # class → seat count
    is_budget: bool = False   # operates as budget-airline plane


@dataclass
class ActiveFlight:
    serial: int           # aircraft serial number
    route_id: str
    depart_day: float     # game_day when departed
    arrive_day: float     # game_day when it lands
    revenue: float        # revenue (dollars) earned on arrival
    going: bool = True    # True = forward through stops, False = reverse
    airport_fees: float = 0.0  # take-off + landing charges (dollars)
    leg_index: int = 0    # which leg of the route (0-based in current direction)


@dataclass
class Route:
    id: str                                           # "JFK-ORD-LHR"
    stops: List[str]                                  # ordered airport codes (2+)
    leg_distances: List[float]                        # km per leg
    ticket_price: float
    aircraft_ids: List[int] = field(default_factory=list)
    active: bool = True
    weekly_pax: int = 0
    last_revenue: float = 0.0
    demand_pool: List[float] = field(default_factory=list)        # per canonical leg
    demand_pool_budget: List[float] = field(default_factory=list)

    @property
    def origin(self) -> str:
        return self.stops[0]

    @property
    def dest(self) -> str:
        return self.stops[-1]

    @property
    def num_legs(self) -> int:
        return len(self.stops) - 1

    @property
    def distance_km(self) -> float:
        return sum(self.leg_distances)

    def leg_pair(self, leg_idx: int, going: bool):
        """Return (from_code, to_code) for the given leg in given direction."""
        n = self.num_legs
        if going:
            return self.stops[leg_idx], self.stops[leg_idx + 1]
        else:
            i = n - 1 - leg_idx
            return self.stops[i + 1], self.stops[i]

    def canonical_leg(self, leg_idx: int, going: bool) -> int:
        """Index into leg_distances / demand_pool for this leg."""
        return leg_idx if going else (self.num_legs - 1 - leg_idx)


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
    difficulty: str = 'normal'   # easy / normal / hard / tycoon
    start_year: int = 1950
    year: int = 1950
    month: int = 1           # 1-12
    day: int = 1             # 1-31
    game_day: float = 0.0    # days elapsed since Jan 1 of start_year
    cash: float = 10_000_000.0  # exact USD
    reputation: float = 50.0 # 0-100
    total_pax: int = 0
    fleet: List[OwnedAircraft] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    active_flights: List[ActiveFlight] = field(default_factory=list)
    finance_history: List[FinancialRecord] = field(default_factory=list)
    events_log: List[str] = field(default_factory=list)
    unlocked_aircraft: List[str] = field(default_factory=list)
    _serial_counter: int = 1
    _triggered_events: List = field(default_factory=list)  # ints (years) + strings (warn keys)

    # Research system
    completed_research: List[str] = field(default_factory=list)
    active_research: Optional[str] = None   # id of current project
    research_progress_days: float = 0.0    # days elapsed on active project

    # Running totals (dollars)
    total_revenue: float = 0.0
    total_costs: float = 0.0

    # Current-period accumulators (reset each month, dollars)
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
        """Return total fleet value in dollars."""
        total = 0.0
        for o in self.fleet:
            ac = get_aircraft(o.ac_id)
            if ac:
                age_factor = max(0.2, 1.0 - (self.year - o.year_acquired) * 0.04)
                total += ac.cost_m * 1_000_000 * age_factor * o.condition
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
        cost = int(ac.cost_m * 1_000_000)
        if cost > self.state.cash:
            return False, f"Need ${cost:,} (have ${int(self.state.cash):,})"
        return True, "OK"

    def buy_aircraft(self, ac: Aircraft) -> Tuple[bool, str]:
        ok, msg = self.can_buy(ac)
        if not ok:
            return False, msg
        cost = int(ac.cost_m * 1_000_000)
        self.state.cash -= cost
        owned = OwnedAircraft(
            ac_id=ac.id,
            name=ac.name,
            serial=self.state.next_serial(),
            year_acquired=self.state.year,
            cabin_config={'economy': ac.passengers},
        )
        self.state.fleet.append(owned)
        self.state.events_log.append(
            f"{self.state.date_str()}: Purchased {ac.name} for ${cost:,}"
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
        sale_price = int(ac.cost_m * 1_000_000 * max(0.15, 1.0 - age * 0.04) * owned.condition)
        self.state.cash += sale_price
        self.state.active_flights = [
            f for f in self.state.active_flights if f.serial != serial
        ]
        self.state.fleet.remove(owned)
        self.state.events_log.append(
            f"{self.state.date_str()}: Sold {owned.name} for ${sale_price:,}"
        )
        return True, f"Sold {owned.name} for ${sale_price:,}"

    # ── Routes ───────────────────────────────────────────────────────────────

    def open_route(self, stops: List[str]) -> Tuple[bool, str]:
        if len(stops) < 2:
            return False, "Need at least 2 airports"
        if len(stops) != len(set(stops)):
            return False, "All stops must be distinct"
        rid = '-'.join(stops)
        if any(r.id == rid for r in self.state.routes):
            return False, "Route already exists"
        cities = [CITY_DICT.get(c) for c in stops]
        if any(c is None for c in cities):
            return False, "Unknown city code"
        leg_distances = []
        for i in range(len(stops) - 1):
            d = great_circle_km(cities[i].lat, cities[i].lon,
                                cities[i+1].lat, cities[i+1].lon)
            leg_distances.append(d)
        total_dist = sum(leg_distances)
        ticket = self._base_ticket(total_dist)
        route = Route(id=rid, stops=stops, leg_distances=leg_distances,
                      ticket_price=ticket)
        self.state.routes.append(route)
        stops_str = '→'.join(stops)
        self.state.events_log.append(
            f"{self.state.date_str()}: Opened route {stops_str} ({total_dist:.0f} km)"
        )
        return True, f"Opened {stops_str}"

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
        if ac and ac.range_km > 0:
            max_leg = max(route.leg_distances) if route.leg_distances else route.distance_km
            if max_leg > ac.range_km:
                return False, (f"{ac.name} range ({ac.range_km} km) is less than "
                               f"the longest leg ({max_leg:.0f} km)")
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

    # ── Research ──────────────────────────────────────────────────────────────

    def unlocked_cabin_classes(self) -> List[str]:
        """Return list of cabin classes the player has unlocked."""
        classes = ['economy']
        for proj_id in self.state.completed_research:
            proj = next((p for p in RESEARCH_PROJECTS if p.id == proj_id), None)
            if proj and proj.unlocks_cabin:
                classes.append(proj.unlocks_cabin)
        return classes

    def start_research(self, project_id: str) -> Tuple[bool, str]:
        s = self.state
        if s.active_research:
            return False, "Already researching a project"
        proj = next((p for p in RESEARCH_PROJECTS if p.id == project_id), None)
        if not proj:
            return False, "Unknown project"
        if project_id in s.completed_research:
            return False, "Already researched"
        if proj.era_min > s.year:
            return False, f"Not available until {proj.era_min}"
        if proj.prerequisite and proj.prerequisite not in s.completed_research:
            prereq = next((p for p in RESEARCH_PROJECTS if p.id == proj.prerequisite), None)
            prereq_name = prereq.name if prereq else proj.prerequisite
            return False, f"Requires: {prereq_name}"
        cost = int(proj.cost_m * 1_000_000)
        if cost > s.cash:
            return False, f"Need ${cost:,} (have ${int(s.cash):,})"
        s.cash -= cost
        s.active_research = project_id
        s.research_progress_days = 0.0
        s.events_log.append(f"🔬 {s.date_str()}: Started research — {proj.name}")
        return True, f"Research started: {proj.name}"

    def cancel_research(self) -> Tuple[bool, str]:
        s = self.state
        if not s.active_research:
            return False, "No active research"
        proj = next((p for p in RESEARCH_PROJECTS if p.id == s.active_research), None)
        # Refund 50% of cost (no full refund — time already spent)
        if proj:
            refund = int(proj.cost_m * 1_000_000 * 0.5)
            s.cash += refund
            s.events_log.append(
                f"🔬 {s.date_str()}: Cancelled research — {proj.name} (${refund:,} refunded)"
            )
        s.active_research = None
        s.research_progress_days = 0.0
        return True, "Research cancelled (50% refunded)"

    def configure_cabin(self, serial: int, config: Dict[str, int]) -> Tuple[bool, str]:
        """Set cabin configuration for an aircraft. config maps class→seats."""
        owned = self.state.get_owned(serial)
        if not owned:
            return False, "Aircraft not found"
        ac = get_aircraft(owned.ac_id)
        if not ac:
            return False, "Unknown aircraft type"
        total_seats = sum(v for v in config.values() if v > 0)
        if total_seats <= 0:
            return False, "Must have at least 1 seat"
        # Weighted check: premium classes take more physical space
        seat_units = sum(v * CABIN_SEAT_SIZES.get(k, 1.0)
                         for k, v in config.items() if v > 0)
        if seat_units > ac.passengers:
            return False, (f"Configuration exceeds aircraft space "
                           f"({seat_units:.1f} units > {ac.passengers} available)")
        # Validate classes are unlocked
        unlocked = self.unlocked_cabin_classes()
        for cls in config:
            if config[cls] > 0 and cls not in unlocked:
                return False, f"{CABIN_DISPLAY_NAMES.get(cls, cls)} not yet researched"
        owned.cabin_config = {k: v for k, v in config.items() if v > 0}
        return True, "Cabin configuration updated"

    def toggle_budget(self, serial: int) -> Tuple[bool, str]:
        """Toggle an aircraft between regular and budget airline operation."""
        if 'budget_subsidiary' not in self.state.completed_research:
            return False, "Research 'Budget Airline Subsidiary' first"
        owned = self.state.get_owned(serial)
        if not owned:
            return False, "Aircraft not found"
        owned.is_budget = not owned.is_budget
        mode = "BUDGET" if owned.is_budget else "regular"
        return True, f"{owned.name} set to {mode} airline mode"

    def airport_demand_info(self, city_code: str) -> List[Dict]:
        """Return demand info for all potential routes from a city code."""
        results = []
        c1 = CITY_DICT.get(city_code)
        if not c1:
            return results
        from data import CITIES
        for c2 in CITIES:
            if c2.code == city_code:
                continue
            dist = great_circle_km(c1.lat, c1.lon, c2.lat, c2.lon)
            pop_factor = math.sqrt(c1.population_m * c2.population_m)
            dist_factor = max(0.3, 1.0 - dist / 20000)
            hub_bonus = 1.4 if (c1.hub_tier == 1 or c2.hub_tier == 1) else 1.0
            rep_factor = 0.5 + self.state.reputation / 100
            daily = int(pop_factor * dist_factor * hub_bonus * rep_factor * 550)
            results.append({
                'dest': c2.code,
                'dest_name': f'{c2.name}, {c2.country}',
                'dist_km': dist,
                'daily_demand': daily,
                'has_route': any(
                    (city_code in r.stops and c2.code in r.stops)
                    for r in self.state.routes),
            })
        results.sort(key=lambda x: -x['daily_demand'])
        return results[:20]  # top 20 by demand

    # ── Economics ─────────────────────────────────────────────────────────────

    def _base_ticket(self, dist_km: float) -> float:
        # Fixed boarding cost + per-km component — short routes are no longer dirt cheap
        base = 80.0 + 0.12 * dist_km
        return min(base, 2200)

    def _leg_daily_demand(self, from_code: str, to_code: str) -> int:
        """One-way daily demand for a specific airport pair."""
        c1 = CITY_DICT.get(from_code)
        c2 = CITY_DICT.get(to_code)
        if not c1 or not c2:
            return 0
        dist = great_circle_km(c1.lat, c1.lon, c2.lat, c2.lon)
        pop_factor = math.sqrt(c1.population_m * c2.population_m)
        # Demand peaks around 600-1500 km; short routes lose to surface transport,
        # very long routes have fewer travellers per city pair.
        if dist < 150:
            dist_factor = dist / 150 * 0.15          # negligible <150 km
        elif dist < 600:
            dist_factor = 0.15 + (dist - 150) / 450 * 0.65  # ramps up to 0.8
        elif dist < 3000:
            dist_factor = 0.8 + (dist - 600) / 2400 * 0.2   # peak zone → 1.0
        else:
            dist_factor = max(0.35, 1.0 - (dist - 3000) / 15000)
        hub_bonus = 1.4 if (c1.hub_tier == 1 or c2.hub_tier == 1) else 1.0
        rep_factor = 0.5 + self.state.reputation / 100
        base = pop_factor * dist_factor * hub_bonus * rep_factor * 420
        demand_mult = 1.0
        if 'frequent_flyer' in self.state.completed_research:
            demand_mult += 0.15
        return max(10, int(base * demand_mult))

    def _route_daily_demand(self, route: Route) -> int:
        """Average daily demand across all legs (used for stats display)."""
        if not route.stops or route.num_legs == 0:
            return 0
        total = sum(self._leg_daily_demand(route.stops[i], route.stops[i+1])
                    for i in range(route.num_legs))
        return total // route.num_legs

    def _schedule_flight(self, owned: OwnedAircraft, route: Route,
                         going: bool = True, depart_day: float = None,
                         leg_index: int = 0):
        """Schedule one leg of the route for this aircraft."""
        s = self.state
        ac = get_aircraft(owned.ac_id)
        if not ac or not route:
            return

        # Which airports and canonical leg index for this leg
        from_code, to_code = route.leg_pair(leg_index, going)
        canonical = route.canonical_leg(leg_index, going)
        leg_dist = route.leg_distances[canonical]

        flight_hours = leg_dist / max(1, ac.speed_kmh) + 0.5
        flight_days = flight_hours / 24.0

        if depart_day is None:
            depart_day = s.game_day
        arrive_day = depart_day + flight_days

        # Leg ticket price proportional to leg distance vs total route
        total_dist = max(1.0, route.distance_km)
        leg_ticket = route.ticket_price * (leg_dist / total_dist)

        # Budget mode: plane uses the budget demand pool and charges half price
        is_budget_flight = (owned.is_budget and
                            'budget_subsidiary' in s.completed_research)
        ticket_mult = 0.5 if is_budget_flight else 1.0

        # Ensure demand pool lists are long enough
        while len(route.demand_pool) <= canonical:
            route.demand_pool.append(-1.0)
        while len(route.demand_pool_budget) <= canonical:
            route.demand_pool_budget.append(-1.0)

        if is_budget_flight:
            pool_val = max(0.0, route.demand_pool_budget[canonical])
        else:
            pool_val = max(0.0, route.demand_pool[canonical])

        # Return legs draw slightly more pax toward origin hub
        if not going:
            pool_val = pool_val * 1.3

        # Build cabin config: fall back to all-economy if unconfigured
        cabin = owned.cabin_config if owned.cabin_config else {'economy': ac.passengers}

        revenue = 0.0
        pax = 0
        has_ife = 'premium_ife' in s.completed_research
        for cls, seats in cabin.items():
            if seats <= 0:
                continue
            if cls == 'supersonic_first' and ac.category != 'supersonic':
                continue
            demand_frac = CABIN_DEMAND_FRACTIONS.get(cls, 1.0)
            cls_demand = int(pool_val * demand_frac)
            cls_pax = min(seats, cls_demand)
            if cls_pax <= 0:
                continue
            load_factor = cls_pax / seats
            yield_adj = 0.8 + load_factor * 0.4
            multiplier = CABIN_MULTIPLIERS.get(cls, 1.0)
            if has_ife and cls in ('business', 'first', 'supersonic_first'):
                multiplier *= 1.25
            revenue += cls_pax * leg_ticket * ticket_mult * multiplier * yield_adj
            pax += cls_pax

        # Graceful fallback if cabin config empty
        if pax == 0:
            pax = min(ac.passengers, int(pool_val))
            load_factor = pax / max(1, ac.passengers)
            revenue = pax * leg_ticket * ticket_mult * (0.8 + load_factor * 0.4)

        # Deduct pax from the appropriate pool
        if is_budget_flight:
            route.demand_pool_budget[canonical] = max(
                0.0, route.demand_pool_budget[canonical] - pax)
        else:
            route.demand_pool[canonical] = max(
                0.0, route.demand_pool[canonical] - pax)

        # Difficulty revenue scaling
        _rev_scale = {'easy': 1.0, 'normal': 1.0, 'hard': 0.88, 'tycoon': 0.75}
        revenue *= _rev_scale.get(s.difficulty, 1.0)

        # Airport fees
        _tier_rate = {1: 0.10, 2: 0.06, 3: 0.03}
        origin_city = CITY_DICT.get(from_code)
        dest_city   = CITY_DICT.get(to_code)
        origin_rate = _tier_rate.get(origin_city.hub_tier if origin_city else 2, 1.20)
        dest_rate   = _tier_rate.get(dest_city.hub_tier   if dest_city   else 2, 1.20)
        airport_fees = pax * (origin_rate + dest_rate)

        s.active_flights.append(ActiveFlight(
            serial=owned.serial,
            route_id=route.id,
            depart_day=depart_day,
            arrive_day=arrive_day,
            revenue=revenue,
            going=going,
            airport_fees=airport_fees,
            leg_index=leg_index,
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

        # Process arrived flights in a loop so that at high game speeds
        # (large delta_hours per tick) chained legs that also arrive within
        # this same tick are caught without waiting for the next tick.
        while True:
            arrived = [f for f in s.active_flights if s.game_day >= f.arrive_day]
            if not arrived:
                break
            for flight in arrived:
                s.active_flights.remove(flight)
                s.cash += flight.revenue
                revenue += flight.revenue
                s.total_revenue += flight.revenue
                s._period_revenue += flight.revenue
                # Airport fees (departure + landing charges)
                s.cash -= flight.airport_fees
                costs += flight.airport_fees
                s.total_costs += flight.airport_fees
                s._period_costs += flight.airport_fees

                owned = s.get_owned(flight.serial)
                route = s.get_route(flight.route_id)
                if owned and route:
                    owned.last_going = flight.going
                    route.last_revenue = flight.revenue
                    ac = get_aircraft(owned.ac_id)
                    if ac:
                        # Use cabin config to estimate pax for stats (use pool snapshot)
                        cabin = owned.cabin_config if owned.cabin_config else {'economy': ac.passengers}
                        canonical = route.canonical_leg(flight.leg_index, flight.going)
                        pool_list = route.demand_pool_budget if owned.is_budget else route.demand_pool
                        pool_snap = max(0.0, pool_list[canonical] if canonical < len(pool_list) else 0.0)
                        pax = sum(
                            min(seats, int(pool_snap * CABIN_DEMAND_FRACTIONS.get(cls, 1.0)))
                            for cls, seats in cabin.items() if seats > 0
                            and not (cls == 'supersonic_first' and ac.category != 'supersonic')
                        ) or min(ac.passengers, int(pool_snap))
                        s.total_pax += pax
                        pax_total += pax
                        # Degradation scales with how long the flight took
                        # (supersonic flights are short so degrade less per flight)
                        flight_days = flight.arrive_day - flight.depart_day
                        degrade_rate = random.uniform(0.00008, 0.00030) * max(0.1, flight_days * 24 / 8)
                        owned.condition = max(0.0, owned.condition - degrade_rate)
                        owned.hours_flown += int(flight_days * 24)

                        # Warn at 10% condition (once)
                        warn_key = f'warn_{owned.serial}'
                        if (0 < owned.condition <= 0.10
                                and warn_key not in s._triggered_events):
                            s._triggered_events.append(warn_key)
                            s.events_log.append(
                                f'⚠️ {s.date_str()}: {owned.name} condition critical '
                                f'({owned.condition*100:.0f}%) — retire soon!'
                            )
                            events_triggered.append(
                                f'{owned.name} condition is critical '
                                f'({owned.condition*100:.0f}%)!\nRetire or sell this aircraft soon.'
                            )

                        # Auto-retire at 0% — sell for scrap
                        if owned.condition <= 0.0:
                            scrap_value = int(
                                get_aircraft(owned.ac_id).cost_m * 1_000_000 * 0.02
                            ) if get_aircraft(owned.ac_id) else 0
                            s.cash += scrap_value
                            # Remove from route and active flights
                            if owned.assigned_route:
                                r = s.get_route(owned.assigned_route)
                                if r and owned.serial in r.aircraft_ids:
                                    r.aircraft_ids.remove(owned.serial)
                            s.active_flights = [
                                f for f in s.active_flights if f.serial != owned.serial
                            ]
                            s.fleet = [o for o in s.fleet if o.serial != owned.serial]
                            s.events_log.append(
                                f'🔧 {s.date_str()}: {owned.name} retired due to wear. '
                                f'Scrapped for ${scrap_value:,}.'
                            )
                            events_triggered.append(
                                f'{owned.name} has been retired!\nThe aircraft wore out and '
                                f'was scrapped for ${scrap_value:,}.'
                            )
                            continue  # skip hours update for retired aircraft
                        days_per_flight = max(0.001, flight.arrive_day - flight.depart_day)
                        route.weekly_pax = int(pax * 7.0 / days_per_flight)
                    # Schedule next leg, or reverse direction when all legs done
                    next_leg = flight.leg_index + 1
                    if next_leg < route.num_legs:
                        # More legs in the same direction
                        self._schedule_flight(owned, route,
                                              going=flight.going,
                                              depart_day=flight.arrive_day,
                                              leg_index=next_leg)
                    else:
                        # Completed all legs — turn around
                        self._schedule_flight(owned, route,
                                              going=not flight.going,
                                              depart_day=flight.arrive_day,
                                              leg_index=0)

        # Refill demand pools for all routes (per leg)
        budget_unlocked = 'budget_subsidiary' in s.completed_research
        for route in s.routes:
            for i in range(route.num_legs):
                daily = self._leg_daily_demand(route.stops[i], route.stops[i + 1])
                hourly_rate = daily / 24.0
                # Grow lists if needed
                while len(route.demand_pool) <= i:
                    route.demand_pool.append(-1.0)
                while len(route.demand_pool_budget) <= i:
                    route.demand_pool_budget.append(-1.0)
                # Initialise on first encounter
                if route.demand_pool[i] < 0:
                    route.demand_pool[i] = float(daily) * 0.5
                if route.demand_pool_budget[i] < 0:
                    route.demand_pool_budget[i] = float(daily) * 2.5
                route.demand_pool[i] = min(
                    float(daily), route.demand_pool[i] + hourly_rate * delta_hours)
                if budget_unlocked:
                    budget_daily = float(daily) * 5.0
                    route.demand_pool_budget[i] = min(
                        budget_daily,
                        route.demand_pool_budget[i] + hourly_rate * 5.0 * delta_hours
                    )

        # Schedule first flight for newly-assigned aircraft (no prior leg)
        for owned in s.fleet:
            if owned.assigned_route:
                in_flight = any(f.serial == owned.serial for f in s.active_flights)
                if not in_flight and owned.last_going is None:
                    route = s.get_route(owned.assigned_route)
                    if route:
                        self._schedule_flight(owned, route, going=True, leg_index=0)

        # Research progress
        if s.active_research:
            proj = next((p for p in RESEARCH_PROJECTS if p.id == s.active_research), None)
            if proj:
                s.research_progress_days += delta_hours / 24.0
                if s.research_progress_days >= proj.duration_days:
                    s.completed_research.append(s.active_research)
                    s.events_log.append(
                        f"🔬 {s.date_str()}: Research complete — {proj.name}!"
                    )
                    events_triggered.append(
                        f"Research breakthrough: {proj.name}\n{proj.effect_desc}"
                    )
                    s.active_research = None
                    s.research_progress_days = 0.0

        # Research cost multipliers
        cost_mult = 1.0
        if 'fuel_efficiency' in s.completed_research:
            cost_mult -= 0.20
        if 'advanced_materials' in s.completed_research:
            cost_mult -= 0.15
        cost_mult = max(0.4, cost_mult)

        # Daily operating costs (accrued proportionally to delta)
        # A realism multiplier scales costs so margins are thin (5-40% depending on aircraft era):
        #   modern jets (monthly_cost_k ~70-350): ~80-100× multiplier → tight margins
        #   pioneer/piston aircraft (~0.2-20): 3-25× → higher % margin but tiny absolute $
        delta_days = delta_hours / 24.0
        for owned in s.fleet:
            ac = get_aircraft(owned.ac_id)
            if ac:
                realism_mult = max(3.0, min(100.0, ac.monthly_cost_k * 1.3))
                daily = ac.monthly_cost_k * 1000 / 30.0 * realism_mult
                if not owned.assigned_route:
                    daily *= 0.4  # parked aircraft cost less
                # Research cost reductions
                ac_mult = cost_mult
                if ('sustainable_aviation' in s.completed_research
                        and ac.fuel_type in ('saf', 'hydrogen')):
                    ac_mult = max(0.3, ac_mult - 0.30)
                c = daily * ac_mult * delta_days
                costs += c
                s.cash -= c
                s.total_costs += c
                s._period_costs += c

        # Fixed overhead (dollars/day), scaled by fleet era so pioneer aircraft
        # aren't bankrupted by costs calibrated for modern jets.
        if s.fleet:
            avg_monthly_k = sum(
                get_aircraft(o.ac_id).monthly_cost_k
                for o in s.fleet if get_aircraft(o.ac_id)
            ) / len(s.fleet)
        else:
            avg_monthly_k = 50.0
        era_scale = min(1.0, avg_monthly_k / 50.0)
        overhead_daily = max(10.0,
                             (len(s.fleet) * 20_000 + len(s.routes) * 10_000) / 90.0 * era_scale)
        if 'budget_subsidiary' in s.completed_research:
            overhead_daily *= 0.70  # 30% overhead reduction
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
                    s.cash += cash_effect * 1000.0  # cash_effect in thousands → dollars
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
    # Starting cash scales with the era so 1903 pioneers start small and
    # 2000s operators start with the capital their era demands.
    # Multiplier is applied to the starter aircraft's purchase price:
    #   easy=50x   →  very generous; plenty of room to experiment
    #   normal=20x →  comfortable; a solid starting fleet
    #   hard=8x    →  lean but workable
    #   tycoon=3x  →  tight; must earn growth quickly
    _difficulty_mult = {'easy': 6.0, 'normal': 2.8, 'hard': 1.5, 'tycoon': 1.1}

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
    starter_cost = int((ac.cost_m if ac else 10.0) * 1_000_000)
    mult = _difficulty_mult.get(difficulty, 2.5)
    cash = int(starter_cost * mult)

    s = GameState(
        airline_name=name,
        hub_code=hub,
        difficulty=difficulty,
        start_year=start_year,
        year=start_year,
        month=1,
        day=1,
        game_day=0.0,
        cash=cash,
        reputation=40.0,
    )
    if ac:
        owned = OwnedAircraft(
            ac_id=starter_id,
            name=ac.name,
            serial=s.next_serial(),
            year_acquired=start_year,
            cabin_config={'economy': ac.passengers},
        )
        s.fleet.append(owned)

    s.events_log.append(f"🛫 {name} founded in {start_year} with hub at {hub}. Good luck!")
    return s
