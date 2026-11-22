"""Copy and dateline locators for the full 24-hour edition. Evidence: SOURCES.tsv."""
import csv
from datetime import date, datetime, time, timezone
from pathlib import Path

DAY = date(2026, 11, 21)
CLOSE = datetime.combine(DAY, time(23, 59, 59), timezone.utc)
CLOCK = CLOSE.strftime("%H:%M UTC")
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


def card(region, tag, place, lat, lon, scene, beat, banner, headline, summary, *, sub="", chip=""):
    return dict(region=region, tag=tag, place=place, lat=lat, lon=lon, scene=scene,
                beat=beat, banner=banner, headline=headline, summary=summary, sub=sub, chip=chip)


def wire(region, place, brief, tag=None):
    return dict(region=region, place=place, brief=brief, tag=tag)


STORIES = [
    card("GLOBAL", "CONFIRMED", "ANTALYA, TÜRKİYE", 36.95, 30.85, "cop", "Climate",
         "COP31: OVERTIME", "Climate talks carry a new draft into Sunday",
         "Fossil fuels and adaptation funding split delegates. The presidency announced "
         "a new text, with objections due by 03:00 UTC Sunday.",
         sub="Day 13 · no final pact", chip="23:39 UTC  /  Reuters dispatch"),
    card("GLOBAL", "UNCONFIRMED", "DARMSTADT, GERMANY", 49.87, 8.62, "mercury", "Mission control",
         "MERCURY: ORBIT WATCH", "BepiColombo makes its bid for Mercury orbit",
         "ESA said at 19:01 UTC the burn should have ended. The mission expected a signal "
         "at 21:37; we could not verify orbital capture by press time.",
         sub="37 min · planned burn", chip="ESA / JAXA  ·  joined orbiters"),
    card("AMERICAS", "OFFICIAL", "JUNÍN, PERU", -10.97, -76.19, "andes", "Earthquake",
         "PERU: QUAKE 6.7", "Peru quake leaves 152 homes uninhabitable",
         "Civil defence records one death and 16 injuries nationwide. The M6.7 quake hit "
         "at 00:09 UTC Saturday, still Friday evening in Peru.",
         sub="129 km deep · Peru's IGP", chip="23:00 UTC  /  INDECI report 6"),
    card("MIDEAST", "OFFICIAL", "MANAMA, BAHRAIN", 26.23, 50.58, "bahrain", "Gulf",
         "BAHRAIN: FIRE", "Bahrain reports fire at industrial site",
         "Ministry reports damage but no injuries after an Iranian attack.",
         chip="Interior ministry  /  Manama"),
    card("EUROPE", "OFFICIAL", "KRYVYI RIH, UKRAINE", 47.91, 33.39, "ukraine", "Ukraine",
         "UKRAINE: 73 HURT", "Two killed in strikes on Kryvyi Rih",
         "City chief counts 73 injured, nine of them children, after Russian strikes.",
         chip="20:02 UTC  /  city toll"),
    card("AFRICA", "REPORTED", "ABU ZABAD AREA, SUDAN", 12.35, 29.25, "kordofan", "Sudan",
         "SUDAN: CIVILIANS", "Relief group accuses RSF of killing civilians",
         "Dar Hamar committee reports women and children killed on Friday.",
         chip="West Kordofan  /  relief report"),
    card("MIDEAST", "OFFICIAL", "KHASAB, OMAN", 26.18, 56.25, "tanker", "Shipping",
         "HORMUZ: SHIPPING", "Two tanker incidents off Oman",
         "UKMTO logged two projectile hits near Khasab. No casualties reported.",
         chip="Strait of Hormuz  /  UKMTO"),
    card("ASIA", "OFFICIAL", "BHUBANESWAR, INDIA", 20.30, 85.82, "flood", "Weather",
         "AKVAN: AFTERMATH", "Odisha puts rivers on watch after Akvan",
         "State orders round-the-clock checks on rivers and reservoirs after heavy rain.",
         chip="Cyclone aftermath  /  Odisha"),
    card("AMERICAS", "CONFIRMED", "GUASAVE, MEXICO", 25.57, -108.47, "sinaloa", "Justice",
         "SINALOA: ARREST", "Mexico confirms capture of ‘El Chapo Isidro’",
         "Fausto Isidro Meza Flores is in custody. Four soldiers died in the operation.",
         chip="Sinaloa  /  defence ministry"),
    card("GLOBAL", "CONFIRMED", "GENEVA, SWITZERLAND", 46.23, 6.14, "geneva", "Technology",
         "AI: NO TREATY", "States keep talking on autonomous weapons",
         "Delegates agreed to work on rules by 2028, not to make them binding.",
         chip="UN arms conference  /  Geneva"),
    card("EUROPE", "CONFIRMED", "NEWCASTLE, ENGLAND", 54.98, -1.62, "football", "Football",
         "ARSENAL: DRAW", "Madueke rescues a point for Arsenal",
         "Newcastle drew 2–2 with the league leaders at St James’ Park.",
         chip="Full time  /  Newcastle v Arsenal"),
    card("AMERICAS", "OFFICIAL", "LAS VEGAS, US", 36.11, -115.16, "vegas", "Formula 1",
         "VEGAS: THE GRID", "Verstappen inherits pole from Antonelli",
         "Antonelli tops Q3 in 1:33.893 but drops five grid places. Russell starts second.",
         chip="Qualifying  /  not the race"),
    card("OCEANIA", "CONFIRMED", "WELLINGTON, NZ", -41.30, 174.78, "cricket", "Cricket",
         "INDIA: 486/4", "Rahul hits 136 as India take a 118-run lead",
         "Gill falls for 98 in the last over of Day 3 against New Zealand.",
         chip="Day 3 stumps  /  Basin Reserve"),
    wire("MIDEAST", "Saudi coalition", "Houthi missiles down: Riyadh 3, west 1"),
    wire("MIDEAST", "Hormuz", "Iran says it downed two US drones", tag="CLAIM"),
    wire("MIDEAST", "Gaza City", "Hospital says strike on food truck killed three"),
    wire("MIDEAST", "Basra", "Fire at Hartha power station spreads to homes"),
    wire("MIDEAST", "Tehran", "Minister says enriched uranium must stay in Iran"),
    wire("EUROPE", "Kyiv", "Zelensky defends Crimean Bridge strikes"),
    wire("EUROPE", "Gulf of Finland", "Crew of 16 leaves burning Sparta II"),
    wire("EUROPE", "Paris", "Ministry counts 21,500 in cost-of-living march"),
    wire("AFRICA", "Bayelsa", "Governor orders inquiry into funeral boat sinking"),
    wire("AFRICA", "Abuja", "CAF reports $31.2m net profit at assembly"),
    wire("AFRICA", "Pretoria", "State funeral set for Phumzile Mlambo-Ngcuka"),
    wire("AMERICAS", "Brasília", "Hospital says Bolsonaro is stable in intensive care"),
    wire("AMERICAS", "Florida", "Flagler limits traffic to 5 mph on flooded roads"),
    wire("ASIA", "Davao", "Air Niugini diversion: all 146 aboard accounted for"),
    wire("ASIA", "Banda Sea", "M6.8 quake off Timor-Leste felt in Darwin"),
    wire("ASIA", "Sejong", "Korail restores service after freight derailment"),
    wire("ASIA", "Manipur", "Six arrested over suspected tainted liquor deaths"),
    wire("ASIA", "Bangkok", "Thailand seeks curbs on mining chemical exports"),
    wire("ASIA", "New Delhi", "Ministry reports progress in Canada trade talks"),
    wire("ASIA", "Cox’s Bazar", "Rohingya welcome ruling but seek safe return"),
    wire("OCEANIA", "Sydney", "Families rally over homebirth insurance rules"),
    wire("OCEANIA", "Melbourne", "Cricket Australia backs Cummins as captain"),
    wire("ASIA", "Qinghai", "M5.6 earthquake strikes Delingha, CENC says"),
    wire("GLOBAL", "Bitcoin", "BTC/USD closes at $60,086 after a $55,106 low"),
    wire("EUROPE", "Turin", "Zverev and Alcaraz win ATP Finals semifinals"),
    wire("EUROPE", "Saint-Denis", "France beat Argentina 45–17 to reach rugby final"),
    wire("AMERICAS", "Barranquilla", "Boca lead Atlético Mineiro 2–0 at cutoff"),
]

with (Path(__file__).resolve().parents[1] / "SOURCES.tsv").open(encoding="utf-8") as fh:
    EVIDENCE = list(csv.DictReader(fh, delimiter="\t"))
for number, item in enumerate(STORIES, 1):
    item["id"] = number
    credits = dict.fromkeys(r["credit"] for r in EVIDENCE if int(r["id"]) == number)
    item["sources"] = ", ".join(credits)

# Six headline figures; ``story`` names the story whose text must hold ``figure`` verbatim.
KPIS = [
    dict(figure="Day 13", story=1, caption=("Antalya’s overtime session;", "no final climate pact adopted")),
    dict(figure="37 min", story=2, caption=("planned Mercury burn;", "not an orbit confirmation")),
    dict(figure="152", story=3, caption=("homes uninhabitable in Peru,", "per the 23:00 UTC report")),
    dict(figure="73", story=5, caption=("injured in Kryvyi Rih,", "including nine children")),
    dict(figure="$60,086", story=37, caption=("bitcoin on Coinbase at", "the Saturday UTC close")),
    dict(figure="486/4", story=13, caption=("India at Saturday stumps;", "118 ahead of New Zealand")),
]

DECK = ("A draft, not a deal, in Antalya  ·  Listening for BepiColombo  ·  "
        "Peru counts the cost of an Andean quake  ·  Bahrain reports an industrial fire")
FOOTBALL_FT = ("Man City 1–1 Fulham", "Chelsea 1–4 Leeds")


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
    assert {int(r["id"]) for r in EVIDENCE} == set(ids)
    for r in EVIDENCE:
        stamp = r["utc"]
        if len(stamp) == 10:  # A dated dispatch, not a fabricated publication minute.
            assert date.fromisoformat(stamp) == DAY, r
        else:
            assert stamp.endswith("Z"), r
            instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            assert instant.date() == DAY and instant <= CLOSE, r
        assert r["credit"] and r["url"].startswith("https://") and r["peg"], r
    keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in keys and s["sources"], s
        if s["id"] <= LEADS:
            assert -90 <= s["lat"] <= 90 and -180 <= s["lon"] <= 180, s
            assert s["tag"] in ("CONFIRMED", "OFFICIAL", "REPORTED", "UNCONFIRMED"), s
            if s["tag"] == "CONFIRMED":
                assert len({r["credit"] for r in EVIDENCE if int(r["id"]) == s["id"]}) >= 2, s
        else:
            assert s["brief"], s
    assert sum(region_counts().values()) == len(STORIES)
    assert all(v > 0 for v in region_counts().values())
    for k in KPIS:
        assert k["figure"] in story_text(story(k["story"])), k
    return True
