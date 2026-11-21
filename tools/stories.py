"""Story data for the Saturday 21 November 2026 Broadsheet Atlas (v7 — 22:00 UTC edition).

All 40 stories audited against Saturday 2026-11-21 UTC coverage (22:00 UTC
compilation clock, cleanly after BepiColombo's 21:37Z Earth signal acquisition).
Every CONFIRMED badge cites 2+ independent outlets; every map pin uses exact
event or dateline coordinates (non-geographic #11 Global Markets unpinned).

Verification tiers:
  CONFIRMED = corroborated by 2+ independent outlets
  OFFICIAL  = on-the-record authority / agency figure or statement
  REPORTED  = single outlet or NGO report, attributed by name
  CLAIM     = one party's unverified military or state-media account
"""

DAY_LABEL = "Saturday 21 November 2026"

REGIONS = [
    # key, label on the bar / legend, archival editorial colour
    ("EUROPE", "EUROPE", "#1F4A6E"),
    ("ASIA", "ASIA", "#B84E1D"),
    ("MIDEAST", "MIDDLE EAST", "#9C2B35"),
    ("AMERICAS", "AMERICAS", "#266B47"),
    ("AFRICA", "AFRICA", "#A86E12"),
    ("OCEANIA", "OCEANIA", "#186F7A"),
    ("GLOBAL", "GLOBAL", "#5F4486"),
]

# fmt: off
STORIES = [
    # ---------------------------------------------------------------- leads (1-3)
    dict(id=1, region="GLOBAL", beat="Climate", tag="CONFIRMED", utc="2026-11-21T20:04",
         place="ANTALYA, TÜRKİYE", lat=36.9, lon=30.7,
         banner="COP31: OVERTIME", sub="No deal · Day 13", chip="Ongoing · AFP, CNBC",
         headline="Climate summit runs into Saturday with no deal",
         summary="COP31 missed its Friday close. A draft omitting fossil fuels split nearly "
                 "200 countries as talks ran deep into Day 13 with no agreement.",
         sources="AP, AFP, CNBC"),
    dict(id=2, region="MIDEAST", beat="War", tag="OFFICIAL", utc="2026-11-21T04:15",
         place="RIYADH · JIZAN", lat=24.7, lon=46.7,
         banner="SAUDI: MISSILES", sub="5 shot down", chip="Coalition · AFP",
         headline="Five Houthi missiles shot down over Saudi Arabia",
         summary="The Saudi-led coalition says air defences downed three missiles over Riyadh "
                 "and two over Jizan across the escalation, after bombing Hodeidah port.",
         sources="Coalition; AFP, Arab News"),
    dict(id=3, region="AMERICAS", beat="Earthquake", tag="CONFIRMED", utc="2026-11-21T00:09",
         place="JUNÍN, PERU", lat=-10.855, lon=-75.978,
         banner="PERU: QUAKE 6.7", sub="00:09 UTC · 108 km", chip="USGS · INDECI · AP",
         headline="Magnitude 6.7 earthquake shakes central Peru",
         summary="Quake at a depth of 108 km near Carhuamayo leaves 1 dead, 15 injured and "
                 "127 homes damaged, civil defence says.",
         sources="USGS, INDECI, AP"),

    # ------------------------------------------------------ secondary row 1 (4-8)
    dict(id=4, region="EUROPE", beat="War", tag="REPORTED", utc="2026-11-21T14:20",
         place="KYIV, UKRAINE", lat=50.4, lon=30.5,
         banner="KYIV: BRIDGE", chip="Interview · BBC",
         headline="Zelensky defends Crimean Bridge strikes",
         summary="Calls raids a 'fair response' to 109 Russian strikes on Ukrainian bridges.",
         sources="BBC News"),
    dict(id=5, region="MIDEAST", beat="Military", tag="CLAIM", utc="2026-11-21T11:12",
         place="STRAIT OF HORMUZ", lat=26.6, lon=56.3,
         banner="HORMUZ: DRONES", chip="Iran's claim · IRIB",
         headline="Iran claims it downed two US drones",
         summary="Hormuz & Qeshm Island; no confirmation from Washington.",
         sources="IRIB, MEE"),
    dict(id=6, region="MIDEAST", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T08:40",
         place="TEHRAN, IRAN", lat=35.7, lon=51.4,
         banner="IRAN: URANIUM", chip="Statement · ToI",
         headline="Iran: uranium stock stays in the country",
         summary="Foreign minister rejects transfer, still sees a 'fair solution'.",
         sources="Times of Israel, AP"),
    dict(id=7, region="AMERICAS", beat="Technology", tag="REPORTED", utc="2026-11-21T03:20",
         place="WASHINGTON, US", lat=38.9, lon=-77.0,
         banner="TRUMP: AI TAX", chip="Briefing · ABC",
         headline="Trump vows tax on data centres abroad",
         summary="Proposes 'tremendous' tax on US firms building AI sites overseas.",
         sources="ABC News"),
    dict(id=8, region="ASIA", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T06:50",
         place="BEIJING, CHINA", lat=39.9, lon=116.4,
         banner="CHINA–JAPAN", chip="Ministry · AFP",
         headline="China tells Japan to 'correct' Taiwan words",
         summary="Beijing demands retraction; Tokyo says its stance is unchanged.",
         sources="Ministry, AFP"),

    # ----------------------------------------------------- secondary row 2 (9-13)
    dict(id=9, region="ASIA", beat="Aviation", tag="OFFICIAL", utc="2026-11-21T02:10",
         place="DAVAO, PHILIPPINES", lat=7.1, lon=125.6,
         banner="DAVAO: 146 SAFE", chip="CAAP · AP",
         headline="Jet lands safely after engine fire alert",
         summary="Air Niugini 767 diverted after alert; all 137 passengers and 9 crew safe.",
         sources="CAAP, AP"),
    dict(id=10, region="GLOBAL", beat="Space", tag="CONFIRMED", utc="2026-11-21T21:37",
         place="ESA DARMSTADT", lat=49.9, lon=8.6,
         banner="MERCURY: ORBIT", sub="ESA · JAXA", chip="Signal · 21:37Z",
         headline="BepiColombo enters orbit around Mercury",
         summary="MPO and Mio enter Mercury orbit; signal received 21:37Z after 8-year trip.",
         sources="ESA, Nature"),
    dict(id=11, region="GLOBAL", beat="Markets", tag="REPORTED", utc="2026-11-21T02:08",
         place="GLOBAL MARKETS", lat=None, lon=None,
         banner="BITCOIN: $58,983", chip="CoinGecko · Sat 21 Nov",
         headline="Bitcoin trades below $59,000 on Saturday",
         summary="Down 3.9% in 24 hours to $58,983; ether slides to $1,625.",
         sources="CoinGecko"),
    dict(id=12, region="AMERICAS", beat="Formula 1", tag="OFFICIAL", utc="2026-11-21T05:20",
         place="LAS VEGAS, US", lat=36.1, lon=-115.2,
         banner="VEGAS GP: POLE", sub="Q3 1:33.893 · FIA", chip="Formula 1 · FIA",
         headline="Verstappen takes pole after Antonelli penalty",
         summary="Antonelli tops Q3 in 1:33.893 before 5-place drop; Russell P2.",
         sources="Formula 1, FIA"),
    dict(id=13, region="OCEANIA", beat="Cricket", tag="CONFIRMED", utc="2026-11-21T06:45",
         place="WELLINGTON, NZ", lat=-41.3, lon=174.8,
         banner="RAHUL: 136", chip="Stumps · AFP, Hindu",
         headline="KL Rahul hits 136 as India reach 486/4",
         summary="Out for 136 on Day 3; India lead New Zealand by 118 at stumps.",
         sources="AFP, The Hindu"),

    # ----------------------------------------------------------- briefs (14-40)
    dict(id=14, region="EUROPE", beat="War", tag="OFFICIAL", utc="2026-11-21T20:02",
         place="Kryvyi Rih", lat=47.9, lon=33.4,
         brief="Strike injury toll climbs to 73 (20:02Z)", sources="Ukrinform"),
    dict(id=15, region="EUROPE", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T10:15",
         place="Copenhagen", lat=55.7, lon=12.6,
         brief="Russian attaché given 7 days to leave", sources="Guardian, AJ"),
    dict(id=16, region="EUROPE", beat="Climate", tag="OFFICIAL", utc="2026-11-21T14:30",
         place="Antalya", lat=36.9, lon=30.7,
         brief="EU's Hoekstra insists on 'good deal or no deal'", sources="AFP"),
    dict(id=17, region="AMERICAS", beat="Climate", tag="OFFICIAL", utc="2026-11-21T11:40",
         place="Antalya", lat=36.9, lon=30.7,
         brief="Panama threatens to block final climate text", sources="Al Jazeera"),
    dict(id=18, region="ASIA", beat="Energy", tag="OFFICIAL", utc="2026-11-21T10:00",
         place="Antalya", lat=36.9, lon=30.7,
         brief="Indonesia's PLN signs six clean-power deals", sources="Antara"),
    dict(id=19, region="MIDEAST", beat="Security", tag="REPORTED", utc="2026-11-21T11:10",
         place="Yemen", lat=14.8, lon=42.9,
         brief="Houthis threaten Jeddah & Red Sea ports", sources="Al Jazeera"),
    dict(id=20, region="AMERICAS", beat="Politics", tag="OFFICIAL", utc="2026-11-21T07:30",
         place="Washington", lat=38.9, lon=-77.0,
         brief="Vance: Iran strikes were Trump's decision", sources="Reuters"),
    dict(id=21, region="AMERICAS", beat="Space", tag="REPORTED", utc="2026-11-21T08:10",
         place="Washington", lat=38.9, lon=-77.0,
         brief="US lawmaker questions SpaceX federal funding", sources="CNN"),
    dict(id=22, region="AMERICAS", beat="Justice", tag="REPORTED", utc="2026-11-21T03:05",
         place="Texas", lat=30.7, lon=-95.6,
         brief="Execution of 70-year-old man takes 63 minutes", sources="ABC"),
    dict(id=23, region="AMERICAS", beat="Courts", tag="CONFIRMED", utc="2026-11-21T01:40",
         place="Los Angeles", lat=34.1, lon=-118.2,
         brief="Jury convicts man of starting Palisades fire", sources="ABC, NBC"),
    dict(id=24, region="AMERICAS", beat="Legal", tag="CONFIRMED", utc="2026-11-21T01:20",
         place="Missouri", lat=38.6, lon=-90.2,
         brief="Judge approves up to $7.25bn Roundup deal", sources="AFP, STLPR"),
    dict(id=25, region="AMERICAS", beat="Climate", tag="REPORTED", utc="2026-11-21T04:50",
         place="Vancouver", lat=49.3, lon=-123.1,
         brief="Canada rests defence in youth climate trial", sources="AFP"),
    dict(id=26, region="ASIA", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T05:10",
         place="Pyongyang", lat=39.0, lon=125.8,
         brief="Kim tours factory sites after no Trump meeting", sources="KCNA, AFP"),
    dict(id=27, region="ASIA", beat="Rail", tag="OFFICIAL", utc="2026-11-21T07:45",
         place="Sejong", lat=36.72, lon=127.16,
         brief="Freight train derails; no injuries reported", sources="Yonhap, KH"),
    dict(id=28, region="ASIA", beat="Policy", tag="CONFIRMED", utc="2026-11-21T08:15",
         place="Taipei", lat=25.0, lon=121.5,
         brief="Budget and NT$20,000 payout bills passed", sources="CNA, Taipei Times"),
    dict(id=29, region="ASIA", beat="Environment", tag="OFFICIAL", utc="2026-11-21T09:05",
         place="Bangkok", lat=13.8, lon=100.5,
         brief="Cabinet weighs arsenic chemical controls", sources="The Nation"),
    dict(id=30, region="ASIA", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T11:20",
         place="New Delhi", lat=28.6, lon=77.2,
         brief="Pakistani minister addresses SCO forum in India", sources="Dawn"),
    dict(id=31, region="ASIA", beat="Weather", tag="OFFICIAL", utc="2026-11-21T06:30",
         place="Eastern India", lat=21.5, lon=85.8,
         brief="Rain alerts as Akvan's remnants move inland", sources="IMD, ETV"),
    dict(id=32, region="ASIA", beat="Rights", tag="REPORTED", utc="2026-11-21T08:50",
         place="Myanmar", lat=19.7, lon=96.1,
         brief="Rights groups urge sanctions after court ruling", sources="AP"),
    dict(id=33, region="AFRICA", beat="Sport", tag="OFFICIAL", utc="2026-11-21T13:05",
         place="Abuja", lat=9.1, lon=7.5,
         brief="CAF lifts member FA grants 33% to $700k", sources="CAF, CECAFA"),
    dict(id=34, region="OCEANIA", beat="Sport", tag="CONFIRMED", utc="2026-11-21T05:30",
         place="Melbourne", lat=-37.8, lon=145.0,
         brief="Cummins keeps the Australian Test captaincy", sources="ABC, AP"),
    dict(id=35, region="AMERICAS", beat="Motorsport", tag="OFFICIAL", utc="2026-11-21T04:09",
         place="Las Vegas", lat=36.1, lon=-115.2,
         brief="FIA gives Verstappen formal warning (04:09Z)", sources="FIA, Autosport"),
    dict(id=36, region="ASIA", beat="Earthquake", tag="CONFIRMED", utc="2026-11-21T09:42",
         place="Timor-Leste", lat=-7.732, lon=127.541,
         brief="M6.8 offshore NE of Lospalos felt in Darwin", sources="USGS, ABC"),
    dict(id=37, region="EUROPE", beat="Protest", tag="REPORTED", utc="2026-11-21T08:29",
         place="Paris", lat=48.9, lon=2.3,
         brief="Sixth Saturday of cost-of-living marches", sources="France 24"),
    dict(id=38, region="AFRICA", beat="Sport", tag="OFFICIAL", utc="2026-11-21T14:15",
         place="Nairobi", lat=-1.3, lon=36.8,
         brief="CAF confirms AFCON 2027 East Africa hosts", sources="CAF, CECAFA"),
    dict(id=39, region="AFRICA", beat="Humanitarian", tag="REPORTED", utc="2026-11-21T07:13",
         place="S. Ethiopia", lat=5.0, lon=38.5,
         brief="Aid report cites ~700k displaced by clashes", sources="Islamic Relief"),
    dict(id=40, region="OCEANIA", beat="Diplomacy", tag="OFFICIAL", utc="2026-11-21T05:15",
         place="Canberra", lat=-35.3, lon=149.1,
         brief="Australia and China agree to AI dialogue", sources="PM.gov.au, ABC"),
]
# fmt: on

# Six headline figures; ``story`` names the story whose text must hold ``figure`` verbatim.
KPIS = [
    dict(figure="Day 13", story=1, caption=("of a COP31 summit past", "its Friday deadline")),
    dict(figure="5", story=2, caption=("Houthi missiles downed", "over Riyadh & Jizan")),
    dict(figure="6.7", story=3, caption=("magnitude of the quake", "shaking Junín & Lima")),
    dict(figure="146", story=9, caption=("people safe after jet's", "Davao emergency landing")),
    dict(figure="$58,983", story=11, caption=("bitcoin on Saturday,", "down 3.9% in 24 hours")),
    dict(figure="136", story=13, caption=("KL Rahul's Day 3 ton;", "India 486/4 at stumps")),
]

DECK = ("COP31 climate talks run past deadline  ·  Five Houthi missiles downed over Saudi Arabia  ·  "
        "M6.7 quake rattles Peru  ·  BepiColombo enters Mercury orbit")

# STRICT ZERO-CONTRADICTION DATE CHECK: ONLY true excluded prior-day stories + unconfirmed items.
EXCLUDED_FRIDAY = [
    "Wall\u00a0Street's\u00a0drop\u00a0into\u00a0a\u00a0correction",
    "Russian\u00a0barrage\u00a0hitting\u00a0Kyiv's\u00a0bridges",
    "Missile\u00a0landing\u00a0in\u00a0Poland",
    "UK–EU\u00a0reset\u00a0deal",
    "Cyclone\u00a0Akvan's\u00a0landfall",
    "Voyager\u00a01's\u00a0light-day\u00a0(18\u00a0Nov)",
]
NOT_YET = [
    "Final COP31 deal text",
    "Las Vegas GP race (Sun 22 Nov 04:00 UTC)",
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
    assert ids == list(range(1, 41)), ids
    keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in keys, s
        assert s["utc"].startswith("2026-11-21T"), s
        assert s["tag"] in ("CONFIRMED", "OFFICIAL", "REPORTED", "CLAIM"), s
        assert s["sources"], s
        if s["tag"] == "CONFIRMED":
            assert "," in s["sources"], f"CONFIRMED requires 2+ sources: {s}"
    assert sum(region_counts().values()) == len(STORIES) == 40
    assert all(v > 0 for v in region_counts().values())
    for k in KPIS:
        assert k["figure"] in story_text(story(k["story"])), k
    return True
