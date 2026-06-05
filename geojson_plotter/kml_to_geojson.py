import json
from pathlib import Path
from typing import Any, Dict, Optional
import re
import xml.etree.ElementTree as ET

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
    match = re.match(r"\{(.+?)\}", root.tag)
    return match.group(1) if match else ""


def _parse_coord_string(text: str):
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


def _find_text(element: ET.Element, tag: str, ns: str) -> str:
    child = element.find(_ns(tag, ns))
    return child.text.strip() if child is not None and child.text else ""


def _build_point(elem: ET.Element, ns: str) -> Dict[str, Any]:
    coords_text = _find_text(elem, "coordinates", ns)
    positions = _parse_coord_string(coords_text)
    return {"type": "Point", "coordinates": positions[0]} if positions else {}


def _build_linestring(elem: ET.Element, ns: str) -> Dict[str, Any]:
    coords_text = _find_text(elem, "coordinates", ns)
    positions = _parse_coord_string(coords_text)
    return {"type": "LineString", "coordinates": positions} if positions else {}


def _build_linear_ring(elem: ET.Element, ns: str):
    coords_text = _find_text(elem, "coordinates", ns)
    positions = _parse_coord_string(coords_text)
    if positions and positions[0] != positions[-1]:
        positions.append(positions[0])
    return positions


def _build_polygon(elem: ET.Element, ns: str) -> Dict[str, Any]:
    outer = elem.find(_ns("outerBoundaryIs", ns))
    if outer is None:
        return {}
    lr = outer.find(_ns("LinearRing", ns))
    if lr is None:
        return {}
    ring = _build_linear_ring(lr, ns)
    if not ring:
        return {}
    rings = [ring]
    for inner in elem.findall(_ns("innerBoundaryIs", ns)):
        lr = inner.find(_ns("LinearRing", ns))
        if lr is None:
            continue
        inner_ring = _build_linear_ring(lr, ns)
        if inner_ring:
            rings.append(inner_ring)
    return {"type": "Polygon", "coordinates": rings}


def _build_geometry(elem: ET.Element, ns: str) -> Dict[str, Any]:
    local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    if local == "Point":
        return _build_point(elem, ns)
    if local == "LineString":
        return _build_linestring(elem, ns)
    if local == "Polygon":
        return _build_polygon(elem, ns)
    if local == "MultiGeometry":
        return _build_multi_geometry(elem, ns)
    return {}


def _build_multi_geometry(elem: ET.Element, ns: str) -> Dict[str, Any]:
    geometries = []
    for child in elem:
        geom = _build_geometry(child, ns)
        if geom:
            geometries.append(geom)
    return {"type": "GeometryCollection", "geometries": geometries} if geometries else {}


def _extract_properties(placemark: ET.Element, ns: str) -> Dict[str, Any]:
    props: Dict[str, Any] = {}
    name = _find_text(placemark, "name", ns)
    if name:
        props["name"] = name
    description = _find_text(placemark, "description", ns)
    if description:
        props["description"] = description
    extended = placemark.find(_ns("ExtendedData", ns))
    if extended is not None:
        for schema_data in extended.findall(_ns("SchemaData", ns)):
            for simple_data in schema_data.findall(_ns("SimpleData", ns)):
                key = simple_data.get("name", "")
                value = simple_data.text.strip() if simple_data.text else ""
                if key:
                    props[key] = value
        for data in extended.findall(_ns("Data", ns)):
            key = data.get("name", "")
            if not key:
                continue
            value_el = data.find(_ns("value", ns))
            value = value_el.text.strip() if value_el is not None and value_el.text else ""
            props[key] = value
    return props


def _iter_placemarks(root: ET.Element, ns: str):
    return root.iter(_ns("Placemark", ns))


def kml_to_geojson(kml_path: str) -> Dict[str, Any]:
    path = Path(kml_path)
    tree = ET.parse(str(path))
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
        if geometry:
            features.append({"type": "Feature", "geometry": geometry, "properties": properties})

    return {"type": "FeatureCollection", "features": features}


def save_geojson(kml_path: str, output_path: Optional[str] = None) -> Path:
    geojson = kml_to_geojson(kml_path)
    output_file = Path(output_path) if output_path else Path(kml_path).with_suffix(".geojson")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(geojson, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_file
