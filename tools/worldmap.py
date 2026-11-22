"""Locator projection and public-domain Natural Earth 1:110m coastlines."""
import json
from pathlib import Path


def outlines():
    features = json.loads(Path(__file__).with_name("ne_110m_land.geojson").read_bytes())["features"]
    land, lakes = [], []
    for feature in features:
        geom = feature["geometry"]
        assert geom["type"] == "Polygon"
        outer, *holes = geom["coordinates"]
        land.append(outer)
        lakes.extend(holes)
    return land, lakes


def project(lon, lat, box, lon0=-174.0, lon1=185.0, lat0=-57.0, lat1=82.0):
    """Equirectangular projection into box=(x, y, w, h)."""
    x, y, w, h = box
    px = x + (lon - lon0) / (lon1 - lon0) * w
    py = y + (lat1 - lat) / (lat1 - lat0) * h
    return px, py
