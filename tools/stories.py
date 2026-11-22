"""Copy and dateline locators for the full 24-hour Saturday UTC edition. Evidence: SOURCES.tsv."""
import csv
from datetime import date, datetime, time, timezone
from pathlib import Path

DAY = date(2026, 11, 21)
OPEN = datetime.combine(DAY, time(0, 0), timezone.utc)
CLOSE = datetime.combine(DAY, time(23, 59, 59), timezone.utc)
CLOCK = CLOSE.strftime("%H:%M UTC")
WINDOW = f"{OPEN:%H:%M}–{CLOSE:%H:%M} UTC"
DAY_LABEL = DAY.strftime("%A %d %B %Y")
LEADS = 13

REGIONS = [
    # key, label on the bar / legend, archival editorial colour
    ("EUROPE", "EUROPE", "#1F4A6E"),
    ("ASIA", "ASIA", "#B84E1D"),
    ("MIDEAST", "MIDDLE EAST", "#9C2B35"),
    ("AMERICAS", "AMERICAS", "#266B47"),
    ("AFRICA", "AFRICA", "#82530D"),
    ("OCEANIA", "OCEANIA", "#186F7A"),
    ("GLOBAL", "GLOBAL", "#5F4486"),
]
TAGS = ("CONFIRMED", "OFFICIAL", "REPORTED", "CLAIM", "UNCONFIRMED")

DECK = (
    "A new draft in Antalya  ·  Bahrain site hit & two Hormuz tankers struck  ·  "
    "Peru counts an Andean quake  ·  Waiting on BepiColombo"
)


def card(region, tag, place, lat, lon, scene, beat, banner, headline, summary, *, sub="", chip=""):
    return dict(region=region, tag=tag, place=place, lat=lat, lon=lon, scene=scene,
                beat=beat, banner=banner, headline=headline, summary=summary, sub=sub, chip=chip)


def wire(region, place, brief, tag=None):
    return dict(region=region, place=place, brief=brief, tag=tag)


STORIES = [
    card("GLOBAL", "CONFIRMED", "ANTALYA, TÜRKİYE", 36.95, 30.85, "cop", "Climate",
         "COP31: OVERTIME", "Climate talks carry a new draft into Sunday",
         "Presidency issues a new text; objections due 03:00 UTC Sunday.",
         sub="Day 13 · no final pact", chip="23:39 UTC  /  Reuters dispatch"),
    card("MIDEAST", "OFFICIAL", "BAHRAIN & OMAN", 26.20, 53.40, "gulf", "Gulf",
         "GULF: BAHRAIN & HORMUZ", "Bahrain industrial site hit; two tankers struck off Oman",
         "Bahrain blames Iran for a plant fire; IRGC claims US radar hits; "
         "UKMTO logs two tankers off Khasab.",
         sub="UKMTO 05:00Z · Bahrain 21:30Z", chip="UKMTO 215-26, 216-26  /  Bahrain Interior Min."),
    card("AMERICAS", "OFFICIAL", "JUNÍN, PERU", -10.97, -76.19, "andes", "Earthquake",
         "PERU: QUAKE 6.7", "Peru quake leaves 152 homes uninhabitable",
         "M6.7 struck 00:09 UTC Saturday; 1 dead, 16 hurt nationwide.",
         sub="129 km deep · Peru’s IGP", chip="23:00 UTC  /  INDECI update"),
    card("EUROPE", "OFFICIAL", "BRUSSELS, BELGIUM", 50.85, 4.35, "trade", "Trade",
         "EU–INDONESIA: TRADE", "EU and Indonesia sign landmark trade pact",
         "Cuts 98.5% of EU tariffs after a decade of talks.",
         chip="CEPA signed  /  Brussels"),
    card("EUROPE", "CONFIRMED", "GULF OF FINLAND", 60.0, 26.2, "baltic", "Baltic",
         "BALTIC: SHIP ABLAZE", "Drone strike sets Russian cargo ship ablaze",
         "16 crew leave Sparta II; Finland suspects Ukraine.",
         chip="06:50 UTC  /  Border Guard"),
    card("AFRICA", "OFFICIAL", "PRAIA, CABO VERDE", 14.93, -23.51, "caboverde", "Election",
         "CABO VERDE: VOTE", "Neves declared re-elected president",
         "Final 15 Nov tally gives him 63.96%.",
         chip="CNE proclamation  /  Sat"),
    card("AMERICAS", "CONFIRMED", "GUASAVE, MEXICO", 25.57, -108.47, "sinaloa", "Security",
         "SINALOA: ARREST", "Mexico captures cartel boss ‘El Chapo Isidro’",
         "Four soldiers and seven gunmen died in raid.",
         chip="Saturday confirmation"),
    card("ASIA", "OFFICIAL", "BHUBANESWAR, INDIA", 20.30, 85.82, "flood", "Weather",
         "CYCLONE AKVAN", "Odisha puts rivers on watch after Cyclone Akvan",
         "Round-the-clock flood checks on rivers.",
         chip="08:06 UTC  /  Sat flood watch"),
    card("ASIA", "OFFICIAL", "BANDA SEA", -7.73, 127.54, "bandasea", "Earthquake",
         "BANDA SEA: QUAKE 6.8", "Deep quake off Timor-Leste rattles Darwin",
         "Struck 132 km deep, NE of Lospalos.",
         chip="09:42 UTC  /  USGS"),
    card("GLOBAL", "UNCONFIRMED", "DARMSTADT, GERMANY", 49.87, 8.62, "mercury", "Mission control",
         "MERCURY: ORBIT WATCH", "BepiColombo makes bid for Mercury orbit",
         "Signal due 21:37 UTC; unverified at close.",
         chip="18:24–19:01 UTC burn"),
    card("EUROPE", "CONFIRMED", "NEWCASTLE, ENGLAND", 54.98, -1.62, "football", "Football",
         "ARSENAL: DRAW", "Madueke rescues a point for Arsenal",
         "Newcastle held leaders 2–2 at St James’.",
         chip="Full time  /  St James’ Park"),
    card("AMERICAS", "OFFICIAL", "LAS VEGAS, US", 36.11, -115.16, "vegas", "Formula 1",
         "VEGAS: THE GRID", "Verstappen inherits pole from Antonelli",
         "Antonelli tops Q3; drops 5 grid spots.",
         chip="Qualifying  /  not the race"),
    card("OCEANIA", "CONFIRMED", "WELLINGTON, NZ", -41.30, 174.78, "cricket", "Cricket",
         "INDIA: 486/4", "India reach 486/4; 118-run lead over NZ",
         "KL Rahul hits 136; Gill falls for 98.",
         chip="Day 3 stumps  /  Basin Reserve"),
    wire("GLOBAL", "Geneva", "No killer-robot treaty; talks run to 2028"),
    wire("MIDEAST", "Hormuz", "Iran says it downed two US drones", tag="CLAIM"),
    wire("MIDEAST", "Gaza City", "Strike on a food truck kills three"),
    wire("MIDEAST", "Basra", "Power-plant gas blast kills four", tag="REPORTED"),
    wire("EUROPE", "Kyiv", "Zelensky defends Crimean Bridge strikes"),
    wire("EUROPE", "Paris", "21,500 join cost-of-living march"),
    wire("MIDEAST", "Tehran", "Enriched uranium stays in Iran, FM says"),
    wire("AFRICA", "Abuja", "CAF posts a $31.2m net profit"),
    wire("AFRICA", "Pretoria", "State funeral set for Mlambo-Ngcuka"),
    wire("AFRICA", "Johannesburg", "Marchers lie down over femicide"),
    wire("AFRICA", "Ibadan", "Tinubu rally mourns boat victims"),
    wire("AMERICAS", "Brasília", "Bolsonaro stable in intensive care"),
    wire("AMERICAS", "Florida", "Flagler caps flooded roads at 5 mph"),
    wire("AMERICAS", "Brazil", "Bred mosquitoes cut dengue by 69%"),
    wire("ASIA", "Manipur", "Six held; toxic liquor toll at 16"),
    wire("ASIA", "Bangkok", "Rare-earth chemical curbs planned"),
    wire("ASIA", "Hanoi", "Assembly passes revised Land Law"),
    wire("ASIA", "Qinghai", "M5.6 earthquake strikes Delingha"),
    wire("OCEANIA", "Sydney", "Families rally over homebirth rules"),
    wire("OCEANIA", "Melbourne", "Board backs Cummins as Test captain"),
    wire("GLOBAL", "Bitcoin", "Ends at $60,086 after $55,106 low"),
    wire("EUROPE", "Turin", "Zverev, Alcaraz win ATP Finals semis"),
    wire("EUROPE", "Saint-Denis", "France beat Argentina 45–17"),
    wire("AMERICAS", "Barranquilla", "Boca lead Mineiro 2–0 at cutoff"),
]

with (Path(__file__).resolve().parents[1] / "SOURCES.tsv").open(encoding="utf-8") as fh:
    EVIDENCE = list(csv.DictReader(fh, delimiter="\t"))
for number, item in enumerate(STORIES, 1):
    item["id"] = number
    credits = list(dict.fromkeys(r["credit"] for r in EVIDENCE if int(r["id"]) == number))
    # Cards print every credit; a wire line has room for its first one only.
    item["sources"] = ", ".join(credits if "headline" in item else credits[:1])

# The day in UTC. Each entry names a lead card and a minute that SOURCES.tsv documents for it,
# so a timestamp on the chronological strip can never drift from the evidence ledger.
TIMELINE = [
    (3, "00:09", "Peru M6.7 quake"),
    (2, "05:00", "Hormuz hits"),
    (5, "06:50", "Baltic ship alert"),
    (9, "09:42", "Banda Sea M6.8"),
    (10, "18:24", "Mercury burn"),
    (3, "23:00", "Peru: 152 homes"),
    (1, "23:39", "COP31 draft"),
]

# Six reconciled headline figures: every phrase in ``needs`` is verified against its named story.
KPIS = [
    dict(story=1, figure="Day 13", caption=("COP31 overtime;", "no final pact adopted"),
         needs=("Day 13", "no final pact")),
    dict(story=2, figure="2 tankers", caption=("struck off Khasab;", "Bahrain plant ablaze"),
         needs=("two tankers", "Khasab", "Bahrain")),
    dict(story=3, figure="152", caption=("homes uninhabitable,", "Peru 23:00 UTC toll"),
         needs=("152 homes uninhabitable",)),
    dict(story=5, figure="16 crew", caption=("leave burning Sparta II", "in Gulf of Finland"),
         needs=("16", "Sparta II")),
    dict(story=34, figure="$60,086", caption=("Bitcoin Coinbase close", "after $55,106 Sat low"),
         needs=("$60,086", "$55,106")),
    dict(story=13, figure="486/4", caption=("India Day 3 stumps;", "118-run lead over NZ"),
         needs=("486/4", "118-run lead")),
]

FOOTBALL_FT = ["Man City 1–1 Fulham", "Chelsea 1–4 Leeds", "Newcastle 2–2 Arsenal (#11)"]

# The date check. Each excluded item carries the UTC date or instant it belongs to; each pending
# item the instant it was due, or None where no time was set. README.md links the reports.
EXCLUDED_LABEL = ("EXCLUDED", "Fri 20 Nov UTC & earlier")
EXCLUDED = [
    ("Houthi missiles over Riyadh (22:53 UTC Fri) & Jazan",
     datetime(2026, 11, 20, 22, 53, tzinfo=timezone.utc)),
    ("Kryvyi Rih missile strike", date(2026, 11, 20)),
    ("Wall Street correction", date(2026, 11, 20)),
    ("Russian barrage on Kyiv bridges", date(2026, 11, 20)),
    ("Missile landing in Poland", date(2026, 11, 20)),
    ("UK–EU reset deal", date(2026, 11, 20)),
    ("Cyclone Akvan landfall", date(2026, 11, 20)),
    ("Voyager 1 light-day (18 Nov)", date(2026, 11, 18)),
]
PENDING_LABEL = ("NOT YET", f"at {CLOCK} close")
PENDING = [
    ("BepiColombo orbit capture (21:37 UTC expected signal unverified at press time)", None),
    ("Final COP31 pact", None),
    ("Las Vegas GP race (Sun 22 Nov, 04:00 UTC)", datetime(2026, 11, 22, 4, 0, tzinfo=timezone.utc)),
    ("Boca–Mineiro result (2–0, still in play)", None),
]


def story(sid):
    for s in STORIES:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def story_text(s):
    return " ".join(str(s.get(k, "")) for k in ("headline", "summary", "brief", "banner", "sub", "chip"))


def region_counts():
    counts = {k: 0 for k, _, _ in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


def instants(sid):
    """UTC instants that SOURCES.tsv documents for one story."""
    return [datetime.fromisoformat(r["utc"].replace("Z", "+00:00"))
            for r in EVIDENCE if int(r["id"]) == sid and r["utc"].endswith("Z")]


def validate():
    ids = [s["id"] for s in STORIES]
    assert {int(r["id"]) for r in EVIDENCE} == set(ids)
    for r in EVIDENCE:
        stamp = r["utc"]
        if len(stamp) == 10:  # A dated dispatch, not a fabricated publication minute.
            assert date.fromisoformat(stamp) == DAY, r
        else:
            assert stamp.endswith("Z"), r
            instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            assert OPEN <= instant <= CLOSE, r
        assert r["credit"] and r["url"].startswith("https://") and r["peg"], r
    keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in keys and s["sources"], s
        if s["id"] <= LEADS:
            assert -90 <= s["lat"] <= 90 and -180 <= s["lon"] <= 180, s
            assert s["tag"] in TAGS and s["chip"], s
            if s["tag"] == "CONFIRMED":
                assert len({r["credit"] for r in EVIDENCE if int(r["id"]) == s["id"]}) >= 2, s
        else:
            assert s["brief"] and s["tag"] in (None,) + TAGS, s
    assert {s["tag"] for s in STORIES if s["tag"]} == set(TAGS)  # the key explains tags in use
    assert sum(region_counts().values()) == len(STORIES)
    assert all(v > 0 for v in region_counts().values())
    assert sum(s["region"] == "AFRICA" for s in STORIES[:LEADS]) >= 1

    for k in KPIS:
        text = story_text(story(k["story"]))
        assert all(phrase in text for phrase in k["needs"]), k
    lead_13 = story(13)
    assert "118-run lead" in " ".join(KPIS[5]["caption"]) and "118-run lead" in lead_13["headline"]

    minutes = [f"{hhmm}" for _, hhmm, _ in TIMELINE]
    assert minutes == sorted(minutes), "timeline must run in UTC order"
    for sid, hhmm, label in TIMELINE:
        assert sid <= LEADS and label, (sid, label)
        assert any(f"{t:%H:%M}" == hhmm for t in instants(sid)), (sid, hhmm)

    for _, when in EXCLUDED:
        assert (when.date() if isinstance(when, datetime) else when) < DAY
        assert not isinstance(when, datetime) or when < OPEN
    assert all(due is None or due > CLOSE for _, due in PENDING)
    return True
