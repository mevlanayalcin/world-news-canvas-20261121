"""Verified Saturday 21 November 2026 UTC stories for the 36-dispatch illustrated poster broadsheet."""
import csv
from datetime import date, datetime, time, timezone
from pathlib import Path

DAY = date(2026, 11, 21)
OPEN = datetime.combine(DAY, time(0, 0), timezone.utc)
CLOSE = datetime.combine(DAY, time(23, 59, 59), timezone.utc)
CLOCK = CLOSE.strftime("%H:%M UTC")
DAY_LABEL = DAY.strftime("%A %d %B %Y")
LEADS = 10

REGIONS = [
    ("EUROPE", "EUROPE", "#1F4A6E"),
    ("ASIA", "ASIA", "#B84E1D"),
    ("MIDEAST", "MIDDLE EAST", "#9C2B35"),
    ("AMERICAS", "AMERICAS", "#266B47"),
    ("AFRICA", "AFRICA", "#8A560E"),
    ("OCEANIA", "OCEANIA", "#166E79"),
    ("GLOBAL", "GLOBAL", "#5F4486"),
]
TAGS = ("CONFIRMED", "OFFICIAL", "REPORTED", "CLAIM", "UNCONFIRMED")


def panel(region, region_pill, tag, place, lat, lon, scene, beat, headline, subhead, meta):
    return dict(
        region=region, region_pill=region_pill, tag=tag, place=place,
        lat=lat, lon=lon, scene=scene, beat=beat, headline=headline,
        subhead=subhead, meta=meta,
    )


def wire(region, place, brief, tag=None):
    return dict(region=region, place=place, brief=brief, tag=tag)


STORIES = [
    # Top Hero Row (2 centerpiece unobstructed illustrated panels)
    panel(
        "GLOBAL", "GLOBAL · CLIMATE", "CONFIRMED", "ANTALYA, TÜRKİYE", 36.95, 30.85, "cop", "CLIMATE",
        "COP31 Enters Overtime",
        "Fossil fuels & finance split talks; new draft awaits Sunday deal",
        "23:39 UTC draft  ·  Reuters, Guardian",
    ),
    panel(
        "MIDEAST", "MIDDLE EAST · SECURITY", "OFFICIAL", "HORMUZ & BAHRAIN", 26.20, 53.40, "gulf", "SECURITY",
        "Gulf Tankers Struck",
        "2 ships hit off Oman; Bahrain plant ablaze; IRGC claims radar hits",
        "05:00Z & 21:30Z  ·  UKMTO, Reuters",
    ),
    # 4 x 2 Illustrated Global Grid (8 large unobstructed cards covering all 7 regions)
    panel(
        "AMERICAS", "AMERICAS", "OFFICIAL", "JUNÍN, PERU", -10.97, -76.19, "andes", "DISASTER",
        "Peru M6.7 Quake",
        "152 homes uninhabitable; 1 dead, 16 hurt",
        "00:09Z / 23:00Z · INDECI",
    ),
    panel(
        "EUROPE", "EUROPE · TRADE", "OFFICIAL", "BRUSSELS", 50.85, 4.35, "trade", "ECONOMY",
        "EU–Indonesia Deal",
        "Cuts 98.5% of EU tariffs after a decade",
        "Brussels · EU",
    ),
    panel(
        "EUROPE", "EUROPE", "CONFIRMED", "GULF OF FINLAND", 60.0, 26.2, "baltic", "MARITIME",
        "Baltic Ship Ablaze",
        "Drone hits Russian Sparta II; 16 crew safe",
        "06:50Z · Border Guard, Reuters",
    ),
    panel(
        "AFRICA", "AFRICA", "OFFICIAL", "PRAIA", 14.93, -23.51, "caboverde", "POLITICS",
        "Cabo Verde Vote",
        "CNE proclaims Neves re-elected (63.96%)",
        "Praia · Sat ruling on 15 Nov vote",
    ),
    panel(
        "ASIA", "ASIA", "OFFICIAL", "ODISHA, INDIA", 20.30, 85.82, "flood", "WEATHER",
        "Odisha Flood Watch",
        "24/7 river alerts after Fri Cyclone Akvan",
        "08:06Z · PTI",
    ),
    panel(
        "AMERICAS", "AMERICAS", "CONFIRMED", "SINALOA, MEXICO", 25.57, -108.47, "sinaloa", "SECURITY",
        "Cartel Boss Arrested",
        "Mexico holds ‘El Chapo Isidro’; 11 killed",
        "Guasave · AP, Reuters",
    ),
    panel(
        "GLOBAL", "GLOBAL · SPACE", "UNCONFIRMED", "DARMSTADT", 49.87, 8.62, "mercury", "SPACE",
        "BepiColombo Bid",
        "18:24 UTC burn; 21:37 signal unverified",
        "ESA · Outcome unverified at close",
    ),
    panel(
        "OCEANIA", "OCEANIA", "CONFIRMED", "WELLINGTON, NZ", -41.30, 174.78, "cricket", "SPORT",
        "India Lead by 118",
        "486/4 Day 3 stumps; KL Rahul 136 vs NZ",
        "06:39Z · The Hindu, Reuters",
    ),
    # 26 Crisp Sourced Wire Dispatches (2 columns x 13 airy rows @ 10.7px Lato-Medium)
    wire("ASIA", "Banda Sea", "M6.8 deep quake rattles Darwin (09:42Z)"),
    wire("GLOBAL", "Geneva", "UN AI-weapons talks extended to 2028"),
    wire("MIDEAST", "Hormuz", "Iran says it downed two US drones", tag="CLAIM"),
    wire("MIDEAST", "Gaza City", "Strike on a food truck kills three"),
    wire("MIDEAST", "Basra", "Power-plant gas blast kills four", tag="REPORTED"),
    wire("MIDEAST", "Tehran", "Enriched uranium stays in Iran, FM says"),
    wire("EUROPE", "Kyiv", "Zelensky defends Crimean Bridge strikes"),
    wire("EUROPE", "Paris", "21,500 join cost-of-living march"),
    wire("AFRICA", "Abuja", "CAF posts a $31.2m net profit"),
    wire("AFRICA", "Johannesburg", "Silent protest against femicide"),
    wire("AFRICA", "Pretoria", "State funeral set for Mlambo-Ngcuka"),
    wire("AFRICA", "Ibadan", "Tinubu mourns Bayelsa boat victims"),
    wire("AMERICAS", "Brasília", "Bolsonaro stable in intensive care"),
    wire("AMERICAS", "Florida", "Flagler caps flooded roads at 5 mph"),
    wire("AMERICAS", "Brazil", "Bred mosquitoes cut dengue by 69%"),
    wire("ASIA", "Manipur", "Six held; toxic liquor toll at 16"),
    wire("ASIA", "Bangkok", "Rare-earth chemical curbs planned"),
    wire("ASIA", "Hanoi", "Assembly passes revised Land Law"),
    wire("ASIA", "Qinghai", "M5.6 earthquake strikes Delingha"),
    wire("OCEANIA", "Sydney", "Families rally over homebirth rules"),
    wire("OCEANIA", "Melbourne", "Board backs Cummins as Test captain"),
    wire("GLOBAL", "Bitcoin", "Closes at $60,086 after $55,106 low"),
    wire("AMERICAS", "Las Vegas", "Verstappen inherits pole (Q3 penalty)"),
    wire("EUROPE", "England", "Premier League: Newcastle 2–2 Arsenal"),
    wire("EUROPE", "Saint-Denis", "Rugby: France beat Argentina 45–17"),
    wire("EUROPE", "Turin", "Zverev, Alcaraz win ATP Finals semis"),
]

# Crisp single-line UTC chronological milestones (every minute backed by SOURCES.tsv).
TIMELINE = [
    (3, "00:09", "Peru M6.7"),
    (2, "05:00", "Hormuz hits"),
    (5, "06:50", "Baltic ship"),
    (11, "09:42", "Banda M6.8"),
    (9, "18:24", "Mercury burn"),
    (2, "21:30", "Bahrain fire"),
    (1, "23:39", "COP31 draft"),
]

EXCLUDED = [
    ("Riyadh (22:53 UTC Fri) & Jazan", datetime(2026, 11, 20, 22, 53, tzinfo=timezone.utc)),
    ("Kryvyi Rih", date(2026, 11, 20)),
    ("Wall St drop", date(2026, 11, 20)),
    ("Kyiv bridges", date(2026, 11, 20)),
    ("Poland missile", date(2026, 11, 20)),
    ("UK–EU deal", date(2026, 11, 20)),
    ("Akvan landfall", date(2026, 11, 20)),
    ("Voyager 1 (18 Nov)", date(2026, 11, 18)),
]
NOTYET = [
    ("BepiColombo capture (21:37 UTC signal unverified)", None),
    ("Final COP31 pact", None),
    ("Las Vegas GP race (Sun 04:00 UTC)", datetime(2026, 11, 22, 4, 0, tzinfo=timezone.utc)),
    ("Boca 2–0 Mineiro (in play)", None),
]

with (Path(__file__).resolve().parents[1] / "SOURCES.tsv").open(encoding="utf-8") as fh:
    EVIDENCE = list(csv.DictReader(fh, delimiter="\t"))
for number, item in enumerate(STORIES, 1):
    item["id"] = number
    credits = list(dict.fromkeys(r["credit"] for r in EVIDENCE if int(r["id"]) == number))
    item["sources"] = ", ".join(credits if "headline" in item else credits[:1])


def region_counts():
    counts = {k: 0 for k, _, _ in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


def instants(sid):
    return [datetime.fromisoformat(r["utc"].replace("Z", "+00:00"))
            for r in EVIDENCE if int(r["id"]) == sid and r["utc"].endswith("Z")]


def validate():
    ids = [s["id"] for s in STORIES]
    assert ids == list(range(1, 37)), ids
    assert {int(r["id"]) for r in EVIDENCE} == set(ids)
    for r in EVIDENCE:
        stamp = r["utc"]
        if len(stamp) == 10:
            assert date.fromisoformat(stamp) == DAY, r
        else:
            assert stamp.endswith("Z"), r
            instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            assert OPEN <= instant <= CLOSE, r
        assert r["credit"] and r["url"].startswith("https://") and r["peg"], r
    region_keys = {k for k, _, _ in REGIONS}
    for s in STORIES:
        assert s["region"] in region_keys and s["sources"], s
        if s["id"] <= LEADS:
            assert -90 <= s["lat"] <= 90 and -180 <= s["lon"] <= 180, s
            assert s["tag"] in TAGS, s
            if s["tag"] == "CONFIRMED":
                assert len({r["credit"] for r in EVIDENCE if int(r["id"]) == s["id"]}) >= 2, s
        else:
            assert s["brief"] and s["tag"] in (None,) + TAGS, s
    assert {s["tag"] for s in STORIES if s["tag"]} == set(TAGS)
    assert all(v > 0 for v in region_counts().values())
    minutes = [hhmm for _, hhmm, _ in TIMELINE]
    assert minutes == sorted(minutes), "timeline must run in UTC order"
    for sid, hhmm, label in TIMELINE:
        assert any(f"{t:%H:%M}" == hhmm for t in instants(sid)), (sid, hhmm)
    for _, when in EXCLUDED:
        assert (when.date() if isinstance(when, datetime) else when) < DAY
    assert all(due is None or due > CLOSE for _, due in NOTYET)
    return True
