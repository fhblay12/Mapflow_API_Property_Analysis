#!/usr/bin/env python3
"""
kml_to_geojson.py
-----------------
Extracts boundary coordinates from a KML file and writes a GeoJSON file.

Usage:
    python kml_to_geojson.py input.kml [output.geojson]

If output path is omitted, the script writes <input_stem>.geojson
in the same directory as the input file.

Supported KML geometry types:
    - Point
    - LineString
    - Polygon  (outer ring + holes)
    - MultiGeometry (nested mix of the above)

Dependencies: only the Python standard library (xml.etree.ElementTree).
"""

import json
import sys
import re
from pathlib import Path
import xml.etree.ElementTree as ET

# ── KML namespace helpers ────────────────────────────────────────────────────

_KML_NAMESPACES = [
    "http://www.opengis.net/kml/2.2",
    "http://earth.google.com/kml/2.2",
    "http://earth.google.com/kml/2.1",
    "http://earth.google.com/kml/2.0",
    "",
]


def _ns(tag: str, ns: str) -> str:
    return f"{{{ns}}}{tag}" if ns else tag


def _detect_namespace(root: ET.Element) -> str:
    m = re.match(r"\{(.+?)\}", root.tag)
    return m.group(1) if m else ""


# ── Coordinate parsing ───────────────────────────────────────────────────────

def _parse_coord_string(text: str) -> list:
    positions = []
    for token in text.strip().split():
        parts = token.split(",")
        if len(parts) < 2:
            continue
        try:
            lon = float(parts[0])
            lat = float(parts[1])
            if len(parts) >= 3 and parts[2].strip():
                alt = float(parts[2])
                positions.append([lon, lat, alt])
            else:
                positions.append([lon, lat])
        except ValueError:
            continue
    return positions


def _find_text(element: ET.Element, tag: str, ns: str) -> str | None:
    child = element.find(_ns(tag, ns))
    return child.text.strip() if child is not None and child.text else None


# ── Geometry builders ────────────────────────────────────────────────────────

def _build_point(elem: ET.Element, ns: str) -> dict | None:
    coords_text = _find_text(elem, "coordinates", ns)
    if not coords_text:
        return None
    positions = _parse_coord_string(coords_text)
    if not positions:
        return None
    return {"type": "Point", "coordinates": positions[0]}


def _build_linestring(elem: ET.Element, ns: str) -> dict | None:
    coords_text = _find_text(elem, "coordinates", ns)
    if not coords_text:
        return None
    positions = _parse_coord_string(coords_text)
    if not positions:
        return None
    return {"type": "LineString", "coordinates": positions}


def _build_linear_ring(elem: ET.Element, ns: str) -> list | None:
    coords_text = _find_text(elem, "coordinates", ns)
    if not coords_text:
        return None
    positions = _parse_coord_string(coords_text)
    if not positions:
        return None
    if positions[0] != positions[-1]:
        positions.append(positions[0])
    return positions


def _build_polygon(elem: ET.Element, ns: str) -> dict | None:
    rings = []
    outer = elem.find(_ns("outerBoundaryIs", ns))
    if outer is None:
        return None
    lr = outer.find(_ns("LinearRing", ns))
    if lr is None:
        return None
    ring = _build_linear_ring(lr, ns)
    if ring is None:
        return None
    rings.append(ring)
    for inner in elem.findall(_ns("innerBoundaryIs", ns)):
        lr = inner.find(_ns("LinearRing", ns))
        if lr is None:
            continue
        ring = _build_linear_ring(lr, ns)
        if ring:
            rings.append(ring)
    return {"type": "Polygon", "coordinates": rings}


def _build_geometry(elem: ET.Element, ns: str) -> dict | None:
    local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if local == "Point":
        return _build_point(elem, ns)
    if local == "LineString":
        return _build_linestring(elem, ns)
    if local == "Polygon":
        return _build_polygon(elem, ns)
    if local == "MultiGeometry":
        return _build_multi_geometry(elem, ns)
    return None


def _build_multi_geometry(elem: ET.Element, ns: str) -> dict | None:
    geometries = []
    for child in elem:
        geom = _build_geometry(child, ns)
        if geom:
            geometries.append(geom)
    if not geometries:
        return None
    return {"type": "GeometryCollection", "geometries": geometries}


# ── Placemark extraction ─────────────────────────────────────────────────────

def _extract_properties(placemark: ET.Element, ns: str) -> dict:
    props: dict = {}
    name = _find_text(placemark, "name", ns)
    if name:
        props["name"] = name
    desc = _find_text(placemark, "description", ns)
    if desc:
        props["description"] = desc
    extended = placemark.find(_ns("ExtendedData", ns))
    if extended is not None:
        for schema_data in extended.findall(_ns("SchemaData", ns)):
            for simple in schema_data.findall(_ns("SimpleData", ns)):
                key = simple.get("name", "")
                val = simple.text.strip() if simple.text else ""
                if key:
                    props[key] = val
        for data in extended.findall(_ns("Data", ns)):
            key = data.get("name", "")
            val_elem = data.find(_ns("value", ns))
            val = val_elem.text.strip() if val_elem is not None and val_elem.text else ""
            if key:
                props[key] = val
    return props


def _iter_placemarks(root: ET.Element, ns: str):
    yield from root.iter(_ns("Placemark", ns))


# ── Main conversion ──────────────────────────────────────────────────────────

def kml_to_geojson(kml_path: str | Path) -> dict:
    kml_path = Path(kml_path)
    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns = _detect_namespace(root)
    features = []
    for placemark in _iter_placemarks(root, ns):
        properties = _extract_properties(placemark, ns)
        geometry = None
        for geo_tag in ("Point", "LineString", "Polygon", "MultiGeometry"):
            geo_elem = placemark.find(_ns(geo_tag, ns))
            if geo_elem is not None:
                geometry = _build_geometry(geo_elem, ns)
                break
        if geometry is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ── Entry point ──────────────────────────────────────────────────────────────

kml_path = Path("KML_Input/Ga North Electoral Areas.kml")       # ← FIX 1: wrap in Path()
geojson_path = Path("geojson_output/Ga_North_Electoral_Areas.geojson")  # ← FIX 2: wrap in Path()

geojson_path.parent.mkdir(parents=True, exist_ok=True)            # ← FIX 3: create output dir if missing

print(f"Reading  : {kml_path}")
geojson = kml_to_geojson(kml_path)
feature_count = len(geojson["features"])

geojson_path.write_text(                                          # now .write_text() works correctly
    json.dumps(geojson, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"Written  : {geojson_path}")
print(f"Features : {feature_count}")

type_counts: dict[str, int] = {}
for f in geojson["features"]:
    t = f["geometry"]["type"]
    type_counts[t] = type_counts.get(t, 0) + 1
for geo_type, count in sorted(type_counts.items()):
    print(f"  {geo_type}: {count}")