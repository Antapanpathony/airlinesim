"""Aircraft and city database for Airline Empire"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Aircraft:
    id: str
    name: str
    manufacturer: str
    year: int
    passengers: int
    range_km: int
    speed_kmh: int
    cost_m: float        # purchase cost in millions USD
    monthly_cost_k: float # monthly operating cost per aircraft (thousands)
    fuel_type: str
    category: str        # pioneer, regional, narrow, wide, supersonic, future
    notes: str = ''

@dataclass
class City:
    code: str
    name: str
    country: str
    lat: float
    lon: float
    population_m: float  # millions
    hub_tier: int        # 1=mega, 2=major, 3=regional

AIRCRAFT_DB: List[Aircraft] = [
    # ── Pioneer Era 1903-1929 ──
    Aircraft('wright',      'Wright Flyer',             'Wright Brothers',   1903,   1,  800,   48,   0.001,   0.05, 'avgas', 'pioneer', 'First powered aircraft'),
    Aircraft('benoist',     'Benoist XIV',              'Benoist',           1914,   2, 1500,   95,   0.005,   0.2,  'avgas', 'pioneer', 'First scheduled airline service (St. Pete–Tampa)'),
    Aircraft('f13',         'Junkers F.13',             'Junkers',           1919,   4, 1500,  170,   0.02,    0.8,  'avgas', 'pioneer', 'First all-metal airliner'),
    Aircraft('fokker7',     'Fokker F.VII-3m',          'Fokker',            1924,   8, 2200,  190,   0.05,    2.0,  'avgas', 'pioneer', 'Iconic trimotor, used on first Pacific crossing'),
    Aircraft('ford5at',     'Ford Trimotor',            'Ford',              1926,  11,  900,  185,   0.07,    2.5,  'avgas', 'regional','The Tin Goose'),

    # ── Golden Age 1930-1945 ──
    Aircraft('b247',        'Boeing 247',               'Boeing',            1933,  10, 1200,  322,   0.15,    4.0,  'avgas', 'regional','First modern airliner'),
    Aircraft('dc2',         'Douglas DC-2',             'Douglas',           1934,  14, 1609,  338,   0.20,    5.0,  'avgas', 'regional','Trans-continental pioneer'),
    Aircraft('dc3',         'Douglas DC-3',             'Douglas',           1936,  28, 2400,  333,   0.25,    5.5,  'avgas', 'regional','Most important airliner ever built'),
    Aircraft('s42',         'Sikorsky S-42',            'Sikorsky',          1934,  32, 4900,  233,   0.30,    8.0,  'avgas', 'regional','Pan Am flying boat'),
    Aircraft('b314',        'Boeing 314 Clipper',       'Boeing',            1938,  74, 5900,  302,   0.50,   12.0,  'avgas', 'wide',   'Pan Am transoceanic luxury clipper'),

    # ── Postwar Piston 1945-1957 ──
    Aircraft('dc4',         'Douglas DC-4',             'Douglas',           1942,  44, 4025,  365,   0.40,   10.0,  'avgas', 'narrow', 'Four-engine transcontinental'),
    Aircraft('constellation','Lockheed Constellation',  'Lockheed',          1943,  60, 8700,  547,   0.60,   15.0,  'avgas', 'narrow', 'The elegant Connie'),
    Aircraft('dc6',         'Douglas DC-6',             'Douglas',           1946,  68, 4800,  507,   0.70,   14.0,  'avgas', 'narrow', 'Pressurized long-range'),
    Aircraft('stratocruiser','Boeing 377 Stratocruiser','Boeing',            1947,  55, 6900,  547,   0.80,   18.0,  'avgas', 'wide',   'Double-deck luxury'),
    Aircraft('l1049',       'Lockheed Super Connie',    'Lockheed',          1951,  95, 9000,  576,   0.90,   18.0,  'avgas', 'narrow', 'Stretched Constellation'),
    Aircraft('dc7',         'Douglas DC-7',             'Douglas',           1953,  95, 7410,  571,   1.00,   20.0,  'avgas', 'narrow', 'Last great piston airliner'),

    # ── Jet Age Dawn 1952-1969 ──
    Aircraft('comet1',      'de Havilland Comet 1',     'de Havilland',      1952,  36, 2800,  787,   1.50,   25.0,  'jet',   'narrow', 'First jet airliner (structural issues)'),
    Aircraft('comet4',      'de Havilland Comet 4',     'de Havilland',      1958,  81, 5190,  809,   2.00,   28.0,  'jet',   'narrow', 'Redesigned, safe Comet'),
    Aircraft('b707',        'Boeing 707-320',           'Boeing',            1958, 149, 9260,  977,   4.50,   45.0,  'jet',   'narrow', 'Launched the commercial jet age'),
    Aircraft('dc8',         'Douglas DC-8',             'Douglas',           1958, 150, 9000,  933,   4.20,   43.0,  'jet',   'narrow', '707 rival'),
    Aircraft('b727',        'Boeing 727-200',           'Boeing',            1963, 189, 4800,  964,   4.80,   40.0,  'jet',   'narrow', 'Three-engine workhorse'),
    Aircraft('dc9',         'Douglas DC-9-50',          'Douglas',           1965, 125, 3095,  906,   3.20,   33.0,  'jet',   'narrow', 'Short/medium range twin'),
    Aircraft('bac111',      'BAC 1-11',                 'BAC',               1965,  89, 2700,  870,   2.80,   28.0,  'jet',   'narrow', 'British rear-engine jet'),
    Aircraft('b737_100',    'Boeing 737-100',           'Boeing',            1968,  85, 2850,  943,   3.00,   30.0,  'jet',   'narrow', 'Shortest 737'),

    # ── Wide Body Era 1969-1982 ──
    Aircraft('b747_100',    'Boeing 747-100',           'Boeing',            1969, 366, 9800,  988,  24.00,  150.0,  'jet',   'wide',   'Queen of the Skies'),
    Aircraft('concorde',    'Concorde',                 'Aérospatiale/BAC',  1969, 100, 7250, 2179,  45.00,  220.0,  'jet',   'supersonic','Mach 2 icon, Paris-London-New York'),
    Aircraft('a300',        'Airbus A300B4',            'Airbus',            1972, 267, 7540,  900,  18.00,  100.0,  'jet',   'wide',   'First Airbus twin-aisle'),
    Aircraft('dc10',        'Douglas DC-10-30',         'Douglas',           1971, 270, 9600,  982,  22.00,  125.0,  'jet',   'wide',   'Three-engine wide body'),
    Aircraft('l1011',       'Lockheed L-1011 TriStar',  'Lockheed',          1972, 302, 9899,  984,  24.00,  130.0,  'jet',   'wide',   'Advanced wide body'),
    Aircraft('b747sp',      'Boeing 747SP',             'Boeing',            1975, 280,15400, 1000,  30.00,  165.0,  'jet',   'wide',   'Ultra-long range 747'),
    Aircraft('b737_200',    'Boeing 737-200',           'Boeing',            1968, 119, 4000,  800,   4.00,   34.0,  'jet',   'narrow', 'Stretched original 737'),

    # ── 1980s Modern Jets ──
    Aircraft('b757',        'Boeing 757-200',           'Boeing',            1982, 200, 7250,  967,  40.00,   80.0,  'jet',   'narrow', 'High-capacity narrow body'),
    Aircraft('b767',        'Boeing 767-300ER',         'Boeing',            1982, 269,11093,  960,  58.00,  115.0,  'jet',   'wide',   'ETOPS pioneer'),
    Aircraft('a310',        'Airbus A310-300',          'Airbus',            1982, 220, 9600,  903,  48.00,   98.0,  'jet',   'wide',   'Shorter A300'),
    Aircraft('a320',        'Airbus A320-200',          'Airbus',            1988, 150, 6150,  903,  50.00,   70.0,  'jet',   'narrow', 'Fly-by-wire pioneer'),
    Aircraft('b747_400',    'Boeing 747-400',           'Boeing',            1988, 416,13450,  988,  90.00,  200.0,  'jet',   'wide',   'Extended range Queen'),

    # ── 1990s Generation ──
    Aircraft('b777_200',    'Boeing 777-200',           'Boeing',            1994, 314, 9700,  905, 120.00,  180.0,  'jet',   'wide',   'Twin-engine wide body'),
    Aircraft('a340',        'Airbus A340-600',          'Airbus',            1993, 380,14600,  905, 115.00,  195.0,  'jet',   'wide',   'Four-engine ultra long range'),
    Aircraft('a330',        'Airbus A330-300',          'Airbus',            1993, 295,13430,  913,  95.00,  165.0,  'jet',   'wide',   'Twin-engine medium/long haul'),
    Aircraft('b737ng',      'Boeing 737-800',           'Boeing',            1998, 162, 5765,  842,  55.00,   74.0,  'jet',   'narrow', 'Next Generation 737'),
    Aircraft('crj900',      'Bombardier CRJ900',        'Bombardier',        1999,  90, 2876,  870,  25.00,   40.0,  'jet',   'regional','Popular regional jet'),
    Aircraft('e195',        'Embraer E195',             'Embraer',           2004, 124, 4260,  870,  30.00,   45.0,  'jet',   'regional','Brazilian regional jet'),

    # ── 2000s Superjumbos ──
    Aircraft('a380',        'Airbus A380-800',          'Airbus',            2005, 555,15200,  903, 280.00,  350.0,  'jet',   'wide',   'World\'s largest passenger airliner'),
    Aircraft('b787_8',      'Boeing 787-8 Dreamliner',  'Boeing',            2009, 242,13620,  914, 155.00,  205.0,  'jet',   'wide',   'Carbon composite revolution'),
    Aircraft('b777_300er',  'Boeing 777-300ER',         'Boeing',            2003, 396,13649,  905, 155.00,  225.0,  'jet',   'wide',   'Long-haul workhorse'),
    Aircraft('a350_900',    'Airbus A350-900',          'Airbus',            2013, 369,15000,  910, 182.00,  235.0,  'jet',   'wide',   'Carbon fiber twin-aisle'),
    Aircraft('b787_9',      'Boeing 787-9',             'Boeing',            2014, 296,14140,  914, 168.00,  215.0,  'jet',   'wide',   'Extended Dreamliner'),
    Aircraft('a320neo',     'Airbus A320neo',           'Airbus',            2016, 165, 6300,  833,  62.00,   72.0,  'jet',   'narrow', 'New Engine Option A320'),
    Aircraft('b737max',     'Boeing 737 MAX 8',         'Boeing',            2017, 178, 6110,  839,  57.00,   68.0,  'jet',   'narrow', 'Re-engined 737'),
    Aircraft('a220_300',    'Airbus A220-300',          'Airbus',            2016, 130, 6300,  871,  42.00,   52.0,  'jet',   'regional','Bombardier C Series'),

    # ── 2020s ──
    Aircraft('b777x',       'Boeing 777X',              'Boeing',            2026, 426,16090,  905, 200.00,  262.0,  'jet',   'wide',   'Folding wingtips, GE9X engines'),
    Aircraft('a321xlr',     'Airbus A321XLR',           'Airbus',            2024, 220, 8700,  833,  66.00,   78.0,  'jet',   'narrow', 'Extra Long Range narrow body'),
    Aircraft('a350_1000',   'Airbus A350-1000',         'Airbus',            2018, 369,16100,  910, 200.00,  252.0,  'jet',   'wide',   'Stretched A350'),

    # ── FUTURE 2027-2050 ──
    Aircraft('boom_overture','Boom Overture',           'Boom Supersonic',   2029,  65, 7870, 1804, 200.00,  300.0,  'saf',      'supersonic','Mach 1.7 sustainable supersonic'),
    Aircraft('boeing_nma',  'Boeing NMA (797)',         'Boeing',            2030, 270, 9260,  920, 140.00,  185.0,  'saf',      'wide',     'New Midmarket Airplane'),
    Aircraft('zunum_hybrid','Zunum Hybrid-Electric',    'Zunum Aero',        2030,  12, 1100,  560,   8.00,   12.0,  'electric', 'regional', 'Hybrid-electric commuter'),
    Aircraft('evtol_50',    'eVTOL Regional 50',        'Various',           2032,  50,  800,  400,  15.00,   20.0,  'electric', 'regional', 'Short-range battery electric'),
    Aircraft('nasa_x66a',   'NASA X-66A TTBW',          'NASA/Boeing',       2033, 180, 7000,  880, 120.00,  120.0,  'saf',      'narrow',   'Transonic Truss-Braced Wing'),
    Aircraft('airbus_zeroe_tf','Airbus ZEROe Turbofan', 'Airbus',            2035, 200, 3700,  900, 180.00,  150.0,  'hydrogen', 'narrow',   'Liquid hydrogen narrow body'),
    Aircraft('hermeus_halcyon','Hermeus Halcyon',       'Hermeus',           2037,  20, 9260, 7400, 500.00,  800.0,  'jet',      'supersonic','Mach 5 hypersonic commercial'),
    Aircraft('airbus_zeroe_bwb','Airbus ZEROe BWB',     'Airbus',            2040, 300, 4000,  850, 250.00,  180.0,  'hydrogen', 'wide',     'Blended Wing Body hydrogen'),
    Aircraft('flying_wing', 'Ultra-Wide Flying Wing',   'Airbus/Boeing',     2045, 800,16000,  950, 500.00,  600.0,  'hydrogen', 'wide',     'Next-century mega-airliner'),
    Aircraft('orbital_hop', 'SpaceX Starship Airliner', 'SpaceX',            2050,1000,  -1, 27000,1200.00, 2000.0, 'methane',  'supersonic','Earth-to-Earth suborbital, 30-min flights'),
]

CITIES: List[City] = [
    # North America
    City('JFK','New York','USA',           40.64, -73.78, 20.0, 1),
    City('LAX','Los Angeles','USA',        33.94,-118.41, 13.0, 1),
    City('ORD','Chicago','USA',            41.98, -87.91, 10.0, 1),
    City('DFW','Dallas','USA',             32.90, -97.04,  7.5, 2),
    City('MIA','Miami','USA',              25.80, -80.28,  6.2, 2),
    City('ATL','Atlanta','USA',            33.64, -84.43,  6.0, 2),
    City('SFO','San Francisco','USA',      37.62,-122.38,  7.8, 2),
    City('SEA','Seattle','USA',            47.45,-122.31,  4.0, 2),
    City('BOS','Boston','USA',             42.36, -71.01,  4.8, 2),
    City('YYZ','Toronto','Canada',         43.68, -79.63,  6.3, 2),
    City('YVR','Vancouver','Canada',       49.19,-123.18,  2.6, 3),
    City('MEX','Mexico City','Mexico',     19.44, -99.07, 21.0, 2),
    # South America
    City('GRU','São Paulo','Brazil',      -23.43, -46.47, 22.0, 2),
    City('GIG','Rio de Janeiro','Brazil', -22.81, -43.25, 13.0, 2),
    City('EZE','Buenos Aires','Argentina',-34.82, -58.54, 15.0, 2),
    City('SCL','Santiago','Chile',        -33.39, -70.79,  7.1, 3),
    City('BOG','Bogotá','Colombia',         4.70, -74.15,  8.0, 3),
    City('LIM','Lima','Peru',             -12.02, -77.11,  9.9, 3),
    # Europe
    City('LHR','London','UK',              51.48,  -0.45, 14.0, 1),
    City('CDG','Paris','France',           49.01,   2.55, 12.0, 1),
    City('FRA','Frankfurt','Germany',      50.03,   8.57,  5.7, 1),
    City('AMS','Amsterdam','Netherlands',  52.31,   4.76,  2.5, 1),
    City('MAD','Madrid','Spain',           40.47,  -3.57,  6.7, 2),
    City('FCO','Rome','Italy',             41.80,  12.24,  4.3, 2),
    City('ZRH','Zurich','Switzerland',     47.46,   8.55,  1.4, 2),
    City('MUC','Munich','Germany',         48.35,  11.79,  1.5, 2),
    City('IST','Istanbul','Turkey',        41.00,  28.71, 15.0, 2),
    City('SVO','Moscow','Russia',          55.97,  37.41, 12.5, 2),
    City('ARN','Stockholm','Sweden',       59.65,  17.92,  1.0, 3),
    City('CPH','Copenhagen','Denmark',     55.62,  12.66,  1.3, 3),
    City('HEL','Helsinki','Finland',       60.32,  24.96,  0.7, 3),
    # Middle East & Africa
    City('DXB','Dubai','UAE',              25.25,  55.36,  3.3, 1),
    City('DOH','Doha','Qatar',             25.26,  51.56,  0.9, 2),
    City('CAI','Cairo','Egypt',            30.12,  31.40, 20.0, 2),
    City('NBO','Nairobi','Kenya',          -1.32,  36.93,  4.4, 2),
    City('JNB','Johannesburg','S. Africa',-26.13,  28.24, 10.0, 2),
    City('CPT','Cape Town','S. Africa',   -33.97,  18.60,  4.6, 3),
    City('LOS','Lagos','Nigeria',           6.58,   3.32, 14.0, 3),
    City('ADD','Addis Ababa','Ethiopia',    8.98,  38.80,  4.6, 3),
    # Asia
    City('NRT','Tokyo','Japan',            35.77, 140.39, 37.4, 1),
    City('PEK','Beijing','China',          40.07, 116.60, 21.5, 1),
    City('PVG','Shanghai','China',         31.14, 121.81, 24.9, 1),
    City('HKG','Hong Kong','China',        22.31, 113.92,  7.5, 1),
    City('SIN','Singapore','Singapore',     1.36, 103.99,  5.8, 1),
    City('BKK','Bangkok','Thailand',       13.69, 100.75, 10.5, 2),
    City('DEL','Delhi','India',            28.57,  77.09, 31.0, 2),
    City('BOM','Mumbai','India',           19.09,  72.87, 20.7, 2),
    City('ICN','Seoul','South Korea',      37.45, 126.45, 10.0, 2),
    City('KUL','Kuala Lumpur','Malaysia',   2.74, 101.71,  8.0, 2),
    # Oceania
    City('SYD','Sydney','Australia',      -33.94, 151.18,  5.3, 1),
    City('MEL','Melbourne','Australia',   -37.67, 144.84,  5.1, 2),
    City('AKL','Auckland','New Zealand',  -37.01, 174.79,  1.7, 3),
]

CITY_DICT = {c.code: c for c in CITIES}

def get_aircraft(ac_id: str) -> Optional[Aircraft]:
    for a in AIRCRAFT_DB:
        if a.id == ac_id:
            return a
    return None

def available_aircraft(year: int) -> List[Aircraft]:
    return [a for a in AIRCRAFT_DB if a.year <= year]

def great_circle_km(lat1, lon1, lat2, lon2) -> float:
    import math
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
