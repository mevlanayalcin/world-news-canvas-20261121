"""Story data for the Saturday 21 November 2026 front page (v2).

Every entry was checked against a live feed item whose publication or event
time falls on Saturday 2026-11-21 UTC (field ``utc`` is the first Saturday
report seen, or the USGS origin time for earthquakes). Zero Friday 20 Nov
stories appear anywhere in STORIES or KPIS.
"""

DAY_LABEL = "Saturday 21 November 2026"

REGIONS = [
    # key, label on the bar / legend, colour
    ("EUROPE", "EUROPE", "#2B5B9E"),
    ("ASIA", "ASIA-PACIFIC", "#C45519"),
    ("MIDEAST", "MIDDLE EAST", "#A62E38"),
    ("AMERICAS", "AMERICAS", "#2B7A4B"),
    ("AFRICA", "AFRICA", "#A87408"),
    ("OCEANIA", "OCEANIA", "#1A8292"),
    ("GLOBAL", "GLOBAL", "#654794"),
]

# fmt: off
STORIES = [
    # ---------------------------------------------------------------- leads (1-3)
    dict(id=1, region="GLOBAL", beat="Climate", tag="CONFIRMED", utc="2026-11-21T14:33",
         place="ANTALYA, TÜRKIYE", lat=36.9, lon=30.7,
         banner="COP31: OVERTIME", sub="No deal · Day 13", chip="Ongoing · AP, Guardian",
         headline="COP31 runs into overtime with no fossil-fuel deal",
         summary="Talks pass Friday's close; EU (\"good deal or no deal\", ~130 backers) and "
                 "Panama reject a draft omitting fossil fuels as venue teardown begins.",
         sources="AP, Guardian, Al-Monitor"),
    dict(id=2, region="MIDEAST", beat="Conflict", tag="OFFICIAL", utc="2026-11-21T04:15",
         place="RIYADH, SAUDI ARABIA", lat=24.7, lon=46.7,
         banner="RIYADH: MISSILES", sub="3 downed · alerts", chip="Coalition · Reuters, AP",
         headline="Saudi air defences down three Houthi missiles over Riyadh",
         summary="The Saudi-led coalition says air defences destroyed three ballistic missiles "
                 "aimed at the capital early Saturday amid citywide alerts; no casualties reported.",
         sources="Coalition; Reuters, AP"),
    dict(id=3, region="EUROPE", beat="War", tag="OFFICIAL", utc="2026-11-21T10:55",
         place="KRYVYI RIH, UKRAINE", lat=47.9, lon=33.4,
         banner="KRYVYI RIH: STRIKE", sub="2 dead · ~60 hurt", chip="Officials · AP, Kyiv Ind.",
         headline="Russian double-tap strike kills 2, injures 60 in Kryvyi Rih",
         summary="Local officials say a 7-year-old boy and a 20-year-old paramedic died when "
                 "drones hit rescuers in Zelensky's hometown after an initial missile strike.",
         sources="Officials; AP, Kyiv Ind."),

    # ------------------------------------------------------ secondary row 1 (4-8)
    dict(id=4, region="EUROPE", beat="Security", tag="OFFICIAL", utc="2026-11-21T12:35",
         place="GULF OF FINLAND", lat=59.9, lon=26.0,
         banner="BALTIC: SHIP HIT", chip="Finnish govt · Reuters",
         headline="Drones set Russian cargo ship ablaze off Finland",
         summary="Kaliningrad-bound Sparta II drifted into Finnish waters; NATO alerted.",
         sources="Reuters, Al Jazeera"),
    dict(id=5, region="AMERICAS", beat="Earthquake", tag="OFFICIAL", utc="2026-11-21T00:09",
         place="CARHUAMAYO, PERU", lat=-11.0, lon=-76.0,
         banner="PERU: QUAKE 6.7", chip="USGS · IGP",
         headline="Magnitude 6.7 quake shakes Peru's Andes at 00:09 UTC",
         summary="Deep 108 km tremor rattled Lima; IGP reports no deaths or tsunami.",
         sources="USGS, IGP"),
    dict(id=6, region="ASIA", beat="Earthquake", tag="OFFICIAL", utc="2026-11-21T09:42",
         place="BANDA SEA, TIMOR-LESTE", lat=-8.1, lon=127.9,
         banner="TIMOR: QUAKE 6.8", chip="USGS · GFZ",
         headline="M6.8 quake strikes off Timor-Leste, felt in Darwin",
         summary="Hit 105 km NE of Lospalos at 09:42 UTC; no tsunami threat.",
         sources="USGS, ABC"),
    dict(id=7, region="ASIA", beat="Aviation", tag="OFFICIAL", utc="2026-11-21T02:10",
         place="DAVAO, PHILIPPINES", lat=7.1, lon=125.6,
         banner="DAVAO: 146 SAFE", chip="Airline · AP",
         headline="Air Niugini jet makes emergency landing; 146 safe",
         summary="Boeing 767 diverted on engine fire alert on HK–Port Moresby flight.",
         sources="CAAP, AP"),
    dict(id=8, region="AMERICAS", beat="Cyber", tag="REPORTED", utc="2026-11-21T13:20",
         place="WASHINGTON, US", lat=38.9, lon=-77.0,
         banner="FBI: NCIC HACK", chip="Reported · Guardian",
         headline="FBI probes apparent NCIC database cyberattack",
         summary="Apparent breach targets key US police warrants and crime records.",
         sources="Guardian, AP"),

    # ----------------------------------------------------- secondary row 2 (9-13)
    dict(id=9, region="AMERICAS", beat="Crime", tag="CONFIRMED", utc="2026-11-21T11:53",
         place="SINALOA, MEXICO", lat=25.6, lon=-108.5,
         banner="SINALOA: CAPTURE", chip="Mexican govt · BBC",
         headline="Mexico captures FBI top-10 fugitive 'Chapo Isidro'",
         summary="Alleged Beltran Leyva chief seized after raid; clashes followed.",
         sources="BBC, Guardian"),
    dict(id=10, region="ASIA", beat="Trade", tag="OFFICIAL", utc="2026-11-21T13:46",
         place="BRUSSELS · JAKARTA", lat=-6.2, lon=106.8,
         banner="EU–INDONESIA DEAL", chip="Signed · Reuters",
         headline="EU and Indonesia sign landmark CEPA trade pact",
         summary="Cuts tariffs on 98.5% of lines after a decade of negotiations.",
         sources="Reuters, Al Jazeera"),
    dict(id=11, region="MIDEAST", beat="Military", tag="REPORTED", utc="2026-11-21T09:10",
         place="TEHRAN, IRAN", lat=35.7, lon=51.4,
         banner="IRAN: LAUNCHER", chip="State TV · AP",
         headline="Iran airs bunker launcher; vows uranium stays",
         summary="IRGC airs dual-missile bunker; FM rejects transferring uranium abroad.",
         sources="IRIB, AP"),
    dict(id=12, region="GLOBAL", beat="AI Arms", tag="CONFIRMED", utc="2026-11-21T05:36",
         place="GENEVA, SWITZERLAND", lat=46.2, lon=6.1,
         banner="GENEVA: AI ARMS", chip="Talks · AP, Reuters",
         headline="UN 'killer robot' talks end with no binding treaty",
         summary="States extend autonomous-weapons talks two years toward 2028 rules.",
         sources="AP, Reuters"),
    dict(id=13, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T12:24",
         place="MCG, MELBOURNE", lat=-37.8, lon=145.0,
         banner="MCG: 188 CHASE", chip="T20I · Sky Sports",
         headline="Australia chase record 188 to beat England at the MCG",
         summary="Nikhil Chaudhary hits 66 and takes 2/21 in 3-wicket T20I win.",
         sources="Sky, ESPNcricinfo"),

    # ----------------------------------------------------------- briefs (14-39)
    dict(id=14, region="EUROPE", beat="Economy", tag="OFFICIAL", utc="2026-11-21T11:51",
         place="Brussels", lat=50.8, lon=4.4,
         brief="EU budget cuts €204bn; 3% Big Tech tax", sources="Council, Reuters"),
    dict(id=15, region="EUROPE", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T10:15",
         place="Copenhagen", lat=55.7, lon=12.6,
         brief="Denmark urges EU Russian visa ban after plot", sources="Kyiv Ind."),
    dict(id=16, region="EUROPE", beat="Protest", tag="CONFIRMED", utc="2026-11-21T08:29",
         place="Paris", lat=48.9, lon=2.3,
         brief="6th straight Sat cost-of-living marches; ~82,500 out", sources="France 24, AA"),
    dict(id=17, region="EUROPE", beat="Justice", tag="CONFIRMED", utc="2026-11-21T12:18",
         place="Tuscany", lat=43.8, lon=11.2,
         brief="Ex-police chief Gianni De Gennaro, 78, found dead", sources="AP"),
    dict(id=18, region="EUROPE", beat="War", tag="OFFICIAL", utc="2026-11-21T06:40",
         place="Yartsevo", lat=55.1, lon=32.7,
         brief="Drone debris sparks Smolensk blaze; 2 killed", sources="Moscow Times"),
    dict(id=19, region="MIDEAST", beat="Energy", tag="OFFICIAL", utc="2026-11-21T06:22",
         place="Basra", lat=30.5, lon=47.8,
         brief="800MW al-Hartha plant gas fire kills 4, hurts 35", sources="Reuters, AJ"),
    dict(id=20, region="MIDEAST", beat="Conflict", tag="REPORTED", utc="2026-11-21T12:29",
         place="Gaza City", lat=31.5, lon=34.5,
         brief="Israeli strike hits food truck, killing at least 3: medics", sources="AP, AJ"),
    dict(id=21, region="MIDEAST", beat="Maritime", tag="REPORTED", utc="2026-11-21T09:30",
         place="Hormuz", lat=26.6, lon=56.3,
         brief="UKMTO tanker alerts; IRGC claims US drones hit", sources="Reuters, AJ"),
    dict(id=22, region="MIDEAST", beat="Security", tag="REPORTED", utc="2026-11-21T11:10",
         place="Yemen", lat=14.8, lon=42.9,
         brief="Houthis threaten Jeddah & Red Sea ports after raids", sources="Al Jazeera"),
    dict(id=23, region="ASIA", beat="Health", tag="OFFICIAL", utc="2026-11-21T14:39",
         place="Manipur", lat=24.8, lon=93.9,
         brief="Toxic-liquor toll hits 16 dead, 200+ hospitalized", sources="NDTV, Hindu"),
    dict(id=24, region="ASIA", beat="Transport", tag="REPORTED", utc="2026-11-21T10:40",
         place="Ranchi", lat=23.3, lon=85.3,
         brief="Cyclone Akvan remnants force 14 flight cancellations", sources="The Hindu"),
    dict(id=25, region="ASIA", beat="Tech", tag="REPORTED", utc="2026-11-21T05:55",
         place="New Delhi", lat=28.6, lon=77.2,
         brief="Opposition protests at Meta offices over bans", sources="Reuters"),
    dict(id=26, region="ASIA", beat="Rail", tag="OFFICIAL", utc="2026-11-21T07:45",
         place="Sejong", lat=36.5, lon=127.3,
         brief="S. Korea freight train derails; 5 cars off, none hurt", sources="Korea Herald"),
    dict(id=27, region="ASIA", beat="Policy", tag="CONFIRMED", utc="2026-11-21T08:15",
         place="Taipei", lat=25.0, lon=121.5,
         brief="Legislature passes national budget & cash payouts", sources="Taipei Times"),
    dict(id=28, region="AFRICA", beat="Sport", tag="OFFICIAL", utc="2026-11-21T13:05",
         place="Abuja", lat=9.1, lon=7.5,
         brief="CAF posts $31.2m profit; 54 FAs back Infantino", sources="CAF, Arab News"),
    dict(id=29, region="AFRICA", beat="Defence", tag="OFFICIAL", utc="2026-11-21T12:44",
         place="Rabat", lat=34.0, lon=-6.8,
         brief="Morocco unveils €366m arms roadmap to 2035", sources="Africanews"),
    dict(id=30, region="AFRICA", beat="Tech", tag="OFFICIAL", utc="2026-11-21T10:37",
         place="Pretoria", lat=-25.7, lon=28.2,
         brief="Ramaphosa sets 90-day deadline for national AI plan", sources="SAnews"),
    dict(id=31, region="AFRICA", beat="Finance", tag="REPORTED", utc="2026-11-21T11:30",
         place="Port Louis", lat=-20.2, lon=57.5,
         brief="African credit-rating talks widen to 15 states", sources="Al Jazeera"),
    dict(id=32, region="AFRICA", beat="Humanitarian", tag="REPORTED", utc="2026-11-21T07:13",
         place="S. Ethiopia", lat=5.0, lon=38.5,
         brief="Aid report cites ~700,000 displaced since Oct", sources="ReliefWeb"),
    dict(id=33, region="AMERICAS", beat="Motorsport", tag="CONFIRMED", utc="2026-11-21T05:54",
         place="Las Vegas", lat=36.1, lon=-115.2,
         brief="Verstappen takes F1 pole after Antonelli penalty", sources="F1, BBC"),
    dict(id=34, region="AMERICAS", beat="Banking", tag="OFFICIAL", utc="2026-11-21T14:05",
         place="Washington", lat=38.9, lon=-77.0,
         brief="Bank Policy Institute warns on agentic AI bank access", sources="BPI"),
    dict(id=35, region="AMERICAS", beat="Climate", tag="CONFIRMED", utc="2026-11-21T04:50",
         place="Vancouver", lat=49.3, lon=-123.1,
         brief="Canada rests defence in youth climate lawsuit", sources="AFP"),
    dict(id=36, region="OCEANIA", beat="Cricket", tag="CONFIRMED", utc="2026-11-21T10:40",
         place="Wellington", lat=-41.3, lon=174.8,
         brief="KL Rahul hits 136, tons in all 4 SENA nations", sources="NDTV"),
    dict(id=37, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T05:30",
         place="Melbourne", lat=-37.8, lon=145.0,
         brief="Pat Cummins retains Australia Test cricket captaincy", sources="ABC"),
    dict(id=38, region="GLOBAL", beat="Markets", tag="CONFIRMED", utc="2026-11-21T11:20",
         place="Markets", lat=None, lon=None,
         brief="Bitcoin rebounds past $60k after dip under $59k", sources="Markets"),
    dict(id=39, region="GLOBAL", beat="Weather", tag="REPORTED", utc="2026-11-21T12:47",
         place="Arctic", lat=71.0, lon=10.0,
         brief="Record-early polar vortex split threatens winter gas stocks", sources="CNBC"),
]
# fmt: on

# Six headline figures; ``story`` names the story whose text must hold ``figure`` verbatim.
KPIS = [
    dict(figure="Day 13", story=1, caption=("of COP31 summit past", "its Friday deadline")),
    dict(figure="3", story=2, caption=("Houthi missiles downed", "over Riyadh, coalition says")),
    dict(figure="60", story=3, caption=("injured, 2 killed in", "Kryvyi Rih double strike")),
    dict(figure="M6.8", story=6, caption=("Banda Sea quake felt", "in Timor-Leste & Darwin")),
    dict(figure="146", story=7, caption=("people safe after jet's", "Davao emergency landing")),
    dict(figure="98.5%", story=10, caption=("of tariff lines cut in", "EU–Indonesia trade pact")),
]

DECK = ("COP31 stretches into overtime  ·  Saudi air defences down 3 missiles over Riyadh  ·  "
        "Double-tap strike hits Kryvyi Rih  ·  Quakes rattle Peru & Timor-Leste")

# Friday 20 November stories left out as yesterday's news, and unconfirmed / upcoming items.
EXCLUDED_FRIDAY = [
    "UK–EU reset deal", "Russian missiles in Poland", "Denmark expels attaché",
    "Palisades arson verdict", "$7.25bn Roundup ruling", "Trump data-centre tax",
    "Argentina $50.75bn LNG", "Haiti–El Salvador prisons", "Iraq\u00a0Jurf\u00a0al-Sakhar",
    "Wall St correction",
]
NOT_YET = [
    "COP31 final text (no deal at press time)",
    "Las Vegas GP race (Sun 22 Nov UTC)",
    "BepiColombo Mercury orbit burn (18:24–19:01 UTC, unconfirmed at press time)",
]


def story(sid):
    for s in STORIES:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def story_text(s):
    return " ".join(str(s.get(k, "")) for k in ("headline", "summary", "brief", "banner", "sub"))


def region_counts():
    counts = {k: 0 for k, _, _ in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


def validate():
    ids = [s["id"] for s in STORIES]
    assert ids == list(range(1, 40)), ids
    keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in keys, s
        assert s["utc"].startswith("2026-11-21T"), s
        assert s["tag"] in ("CONFIRMED", "OFFICIAL", "REPORTED"), s
        assert s["sources"], s
    assert sum(region_counts().values()) == len(STORIES) == 39
    assert all(v > 0 for v in region_counts().values())
    for k in KPIS:
        assert k["figure"] in story_text(story(k["story"])), k
    return True
