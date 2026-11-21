"""Story data for the Saturday 21 November 2026 front page.

Every entry was checked against a live feed item whose publication time
falls on 2026-11-21 UTC (field ``utc`` is the first Saturday report seen,
or the event time from USGS for earthquakes). ``tag`` says how sure the
claim is: CONFIRMED (several outlets report it as fact), OFFICIAL (an
authority's figure or statement), REPORTED (one side's claim or a single
outlet / NGO, attributed by name).
"""

DAY_LABEL = "Saturday 21 November 2026"

REGIONS = [
    # key, label on the bar, colour
    ("EUROPE", "EUROPE", "#2F5D9E"),
    ("ASIA", "ASIA-PACIFIC", "#C2571A"),
    ("AMERICAS", "AMERICAS", "#2E7D4F"),
    ("MIDEAST", "MIDDLE EAST", "#A8323A"),
    ("AFRICA", "AFRICA", "#B8860B"),
    ("OCEANIA", "OCEANIA", "#1F8A99"),
    ("GLOBAL", "GLOBAL/SCI.", "#6A4C93"),
]

# fmt: off
STORIES = [
    # ---------------------------------------------------------------- leads
    dict(id=1, region="GLOBAL", beat="Climate", tag="CONFIRMED", utc="2026-11-21T14:33",
         place="ANTALYA, TURKEY", lat=36.9, lon=30.7, ribbon="COP31 · OVERTIME DAY",
         headline="COP31 runs into overtime with no deal on fossil fuels",
         summary="Talks in Antalya overran Friday's deadline. The EU believes about 130 countries "
                 "back naming fossil fuels in the final text; none adopted by mid-afternoon UTC.",
         sources="Guardian, DW, AP"),
    dict(id=2, region="GLOBAL", beat="Space", tag="OFFICIAL", utc="2026-11-21T09:48",
         place="ESA MISSION CONTROL, DARMSTADT", lat=49.9, lon=8.6, ribbon="MERCURY ORBIT DAY",
         headline="BepiColombo's day to enter orbit around Mercury",
         summary="ESA's timeline sets 21 November for the European-Japanese probe to enter "
                 "Mercury orbit after an 8-year, 9-flyby trip; orbiters MPO and Mio split 9-10 Dec.",
         sources="ESA, Space.com, Mashable"),
    dict(id=3, region="AMERICAS", beat="Crime", tag="CONFIRMED", utc="2026-11-21T11:53",
         place="GUASAVE, SINALOA, MEXICO", lat=25.6, lon=-108.5, ribbon="FBI TOP-10 FUGITIVE HELD",
         headline="Mexican army captures FBI-wanted 'Chapo Isidro'",
         summary="Fausto Isidro Meza Flores, alleged Beltran Leyva gang boss on the FBI's 10 most "
                 "wanted list, was seized after a shoot-out; violence followed.",
         sources="Mexican army; BBC, NYT"),
    # ------------------------------------------------------------ secondary
    dict(id=4, region="EUROPE", beat="Security", tag="OFFICIAL", utc="2026-11-21T12:35",
         place="GULF OF FINLAND", lat=59.9, lon=26.0, ribbon="BALTIC DRONE STRIKE",
         headline="Drones set Russia-bound cargo ship ablaze off Finland",
         summary="Kaliningrad-bound ship drifted into Finnish waters; NATO alerted.",
         sources="Finnish govt; France 24"),
    dict(id=5, region="EUROPE", beat="War", tag="OFFICIAL", utc="2026-11-21T10:55",
         place="KRYVYI RIH, UKRAINE", lat=47.9, lon=33.4, ribbon="UKRAINE WAR",
         headline="Russian missiles kill 2 in Zelensky's home city",
         summary="Dozens wounded, local officials say, after Putin vowed a 'painful' reply.",
         sources="officials; AP, DW"),
    dict(id=6, region="GLOBAL", beat="Arms control", tag="CONFIRMED", utc="2026-11-21T05:36",
         place="GENEVA, SWITZERLAND", lat=46.2, lon=6.1, ribbon="AI WEAPONS",
         headline="UN 'killer robot' talks end with no binding ban",
         summary="States aim for rules by 2028 after Russian pushback.",
         sources="Reuters, NPR"),
    dict(id=7, region="AMERICAS", beat="Earthquake", tag="OFFICIAL", utc="2026-11-21T00:09",
         place="CARHUAMAYO, PERU", lat=-11.0, lon=-76.0, ribbon="ANDES QUAKE",
         headline="M6.7 quake shakes Peru's Andes at 00:09 UTC",
         summary="Lima residents ran outside; no damage reported.",
         sources="USGS, IGP; Reuters"),
    dict(id=8, region="ASIA", beat="Earthquake", tag="OFFICIAL", utc="2026-11-21T09:42",
         place="BANDA SEA, TIMOR-LESTE", lat=-8.1, lon=127.9, ribbon="BANDA SEA QUAKE",
         headline="M6.8 quake hits off Timor-Leste, rattles Darwin",
         summary="Struck 105 km NE of Lospalos at 09:42 UTC; felt in Australia's Top End.",
         sources="USGS, GFZ; ABC"),
    dict(id=9, region="MIDEAST", beat="Energy", tag="OFFICIAL", utc="2026-11-21T06:22",
         place="BASRA, IRAQ", lat=30.5, lon=47.8, ribbon="POWER PLANT FIRE",
         headline="Fire at Basra power station kills at least 4",
         summary="Hartha plant blaze injured about 30; now contained.",
         sources="Reuters, Al Jazeera"),
    dict(id=10, region="ASIA", beat="Health", tag="OFFICIAL", utc="2026-11-21T14:39",
         place="MANIPUR, INDIA", lat=24.8, lon=93.9, ribbon="TOXIC LIQUOR",
         headline="Manipur toxic-liquor toll rises to 16 dead",
         summary="Police hold six; hundreds treated after drinking spurious liquor.",
         sources="Manipur Police; The Hindu"),
    dict(id=11, region="AFRICA", beat="Humanitarian", tag="REPORTED", utc="2026-11-21T07:13",
         place="SOUTHERN ETHIOPIA", lat=6.0, lon=38.0, ribbon="DISPLACEMENT",
         headline="700,000 displaced by fighting in southern Ethiopia",
         summary="Aid group cites ethnic clashes over land.",
         sources="Islamic Relief; Africanews"),
    dict(id=12, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T12:24",
         place="MCG, MELBOURNE", lat=-37.8, lon=145.0, ribbon="CRICKET · 1ST T20",
         headline="Australia chase 188 to beat England at the MCG",
         summary="Nikhil Chaudhary starred in a 3-wicket win.",
         sources="BBC Sport, ESPNcricinfo"),
    dict(id=13, region="MIDEAST", beat="Military", tag="REPORTED", utc="2026-11-21T09:30",
         place="STRAIT OF HORMUZ", lat=26.6, lon=56.3, ribbon="IRAN CLAIM",
         headline="Iran's IRGC says it shot down 2 US drones",
         summary="Iranian claim; US sanctions four 'oil trustees'.",
         sources="IRGC via Al Jazeera"),
    # ---------------------------------------------------------------- briefs
    dict(id=14, region="EUROPE", beat="Economy", tag="OFFICIAL", utc="2026-11-21T11:51",
         place="Brussels", brief="EU budget plan adds Big Tech tax, trims €204bn", sources="SCMP"),
    dict(id=15, region="EUROPE", beat="Protest", tag="CONFIRMED", utc="2026-11-21T08:29",
         place="France", brief="6th straight Saturday of cost-of-living protests", sources="France 24"),
    dict(id=16, region="EUROPE", beat="Culture", tag="CONFIRMED", utc="2026-11-21T12:00",
         place="London", brief="Princess of Wales on cancer in BBC film 'Heal'", sources="BBC"),
    dict(id=17, region="GLOBAL", beat="Science", tag="REPORTED", utc="2026-11-21T12:00",
         place="Beijing", brief="Lunar chief urges moon water, oxygen test by 2030", sources="SCMP"),
    dict(id=18, region="GLOBAL", beat="Weather", tag="REPORTED", utc="2026-11-21T12:47",
         place="Arctic", brief="Record-early polar vortex split threatens gas stocks", sources="CNBC"),
    dict(id=19, region="AMERICAS", beat="Justice", tag="OFFICIAL", utc="2026-11-21T09:50",
         place="Haiti", brief="Deal with El Salvador to build three new prisons", sources="Africanews"),
    dict(id=20, region="AMERICAS", beat="Energy", tag="OFFICIAL", utc="2026-11-21T11:01",
         place="Argentina", brief="Milei approves $50.75bn YPF-led LNG plan", sources="BA Times"),
    dict(id=21, region="AMERICAS", beat="Motorsport", tag="CONFIRMED", utc="2026-11-21T05:54",
         place="Las Vegas", brief="Verstappen on F1 pole after Antonelli penalty", sources="BBC Sport"),
    dict(id=22, region="MIDEAST", beat="Conflict", tag="REPORTED", utc="2026-11-21T12:29",
         place="Gaza", brief="Israeli attacks kill at least four Palestinians", sources="Al Jazeera"),
    dict(id=23, region="MIDEAST", beat="Security", tag="CONFIRMED", utc="2026-11-21T07:11",
         place="Iraq", brief="Troops deploy in Iran-backed militia stronghold", sources="NYT, NBC"),
    dict(id=24, region="MIDEAST", beat="Shipping", tag="REPORTED", utc="2026-11-21T07:57",
         place="Oman", brief="UKMTO logs 2 tanker incidents; Iran cites a mine", sources="Reuters"),
    dict(id=25, region="AFRICA", beat="Obituary", tag="CONFIRMED", utc="2026-11-21T05:44",
         place="South Africa", brief="Ex-deputy president Mlambo-Ngcuka dies, 71", sources="AP, Reuters"),
    dict(id=26, region="AFRICA", beat="Defence", tag="OFFICIAL", utc="2026-11-21T12:44",
         place="Morocco", brief="€366m plan for a national arms industry by 2035", sources="Africanews"),
    dict(id=27, region="AFRICA", beat="Health", tag="REPORTED", utc="2026-11-21T10:58",
         place="DR Congo", brief="Violence and distrust hamper Ebola fight: HI", sources="AFP"),
    dict(id=28, region="AFRICA", beat="Technology", tag="REPORTED", utc="2026-11-21T10:37",
         place="South Africa", brief="Ramaphosa returns with AI start-up fund plan", sources="News24"),
    dict(id=29, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T10:40",
         place="Wellington", brief="KL Rahul ton puts India 118 ahead of NZ", sources="ESPNcricinfo"),
    dict(id=30, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T05:08",
         place="Melbourne", brief="North Melbourne, Melbourne reach AFLW final", sources="ABC"),
    dict(id=31, region="OCEANIA", beat="Wildlife", tag="REPORTED", utc="2026-11-21T06:46",
         place="New Zealand", brief="3rd dead penguin in a week raises bird-flu fears", sources="Stuff"),
    dict(id=32, region="OCEANIA", beat="Obituary", tag="CONFIRMED", utc="2026-11-21T10:00",
         place="Australia", brief="1956 Olympic swim champion Jon Henricks dies, 91", sources="ABC"),
    dict(id=33, region="ASIA", beat="Trade", tag="OFFICIAL", utc="2026-11-21T13:46",
         place="Indonesia", brief="Signs 'ambitious' trade deal with the EU", sources="SCMP"),
    dict(id=34, region="ASIA", beat="Technology", tag="REPORTED", utc="2026-11-21T05:55",
         place="India", brief="Opposition protests at Meta offices over bans", sources="Reuters"),
    dict(id=35, region="ASIA", beat="Transport", tag="REPORTED", utc="2026-11-21T10:40",
         place="Ranchi", brief="Cyclone Akvan forces 14 flight cancellations", sources="The Hindu"),
]
# fmt: on

# Six headline figures; ``story`` names the story whose text must hold ``figure`` verbatim.
KPIS = [
    dict(figure="130", story=1, caption=("countries back fossil-fuel", "wording at COP31, EU says")),
    dict(figure="700,000", story=11, caption=("displaced by fighting in", "southern Ethiopia")),
    dict(figure="M6.8", story=8, caption=("Banda Sea quake felt in", "Timor-Leste and Darwin")),
    dict(figure="16", story=10, caption=("dead in Manipur's", "toxic-liquor poisoning")),
    dict(figure="2028", story=6, caption=("UN target for rules on", "AI 'killer robots'")),
    dict(figure="$50.75bn", story=20, caption=("Argentina LNG export", "project approved")),
]

# The day in UTC: first report times from the feeds (USGS event times for quakes).
TIMELINE = [
    ("00:09", "Peru M6.7 quake"),
    ("04:00", "Killer-robot talks end"),
    ("05:20", "Verstappen on pole"),
    ("06:22", "Basra plant fire"),
    ("09:30", "IRGC drone claim"),
    ("09:42", "Timor M6.8 quake"),
    ("10:55", "Kryvyi Rih strike"),
    ("11:53", "'Chapo Isidro' held"),
    ("12:35", "Ship hit off Finland"),
    ("14:33", "COP31 still talking"),
]

DECK = ("COP31 overruns its deadline  ·  BepiColombo's Mercury orbit day  ·  Mexico seizes an "
        "FBI top-10 fugitive  ·  Drones hit a ship off Finland  ·  Missiles strike Kryvyi Rih")

# Friday 20 November stories left out as yesterday's news, and things that have not happened yet.
EXCLUDED_FRIDAY = [
    "UK-EU reset deal", "Russian missiles land in Poland", "Denmark expels Russian diplomat",
    "Nvidia SEC probe report", "S&P 500 correction close", "GTA VI $3.8bn first day",
    "Riemann proof claim", "Zecler police verdict", "Bolsonaro in hospital", "Kane ankle injury",
]
NOT_YET = [
    "COP31 final text (not adopted at press time)", "Las Vegas GP race (Sun 22 Nov UTC)",
    "Hong Kong Election Committee poll (Sun 22 Nov)", "Victoria state election (28 Nov)",
    "BepiColombo MPO/Mio split (9-10 Dec)",
]


def story(sid):
    for s in STORIES:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def story_text(s):
    return " ".join(str(s.get(k, "")) for k in ("headline", "summary", "brief", "ribbon"))


def region_counts():
    counts = {k: 0 for k, _, _ in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


def validate():
    ids = [s["id"] for s in STORIES]
    assert ids == list(range(1, 36)), ids
    keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in keys, s
        assert s["utc"].startswith("2026-11-21T"), s
        assert s["tag"] in ("CONFIRMED", "OFFICIAL", "REPORTED"), s
        assert s["sources"], s
    assert sum(region_counts().values()) == len(STORIES) == 35
    assert all(v > 0 for v in region_counts().values())
    for k in KPIS:
        assert k["figure"] in story_text(story(k["story"])), k
    stamps = [t for t, _ in TIMELINE]
    assert stamps == sorted(stamps), stamps
    return True
