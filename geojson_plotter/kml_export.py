import json
import os
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent
from typing import Any, Dict, List


def json_to_kml(json_path: str, output_dir: str = "finaljson_output") -> Path:
    json_path = Path(json_path)
    with json_path.open("r", encoding="utf-8") as f:
        buildings: List[Dict[str, Any]] = json.load(f)

    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")
    name = SubElement(document, "name")
    name.text = "Buildings"

    for i, building in enumerate(buildings):
        placemark = SubElement(document, "Placemark")
        pm_name = SubElement(placemark, "name")
        pm_name.text = f"Building {i + 1}"

        desc = SubElement(placemark, "description")
        desc.text = "\n".join(f"{k}: {v}" for k, v in building.items() if v is not None)

        extended = SubElement(placemark, "ExtendedData")
        for key, value in building.items():
            data = SubElement(extended, "Data", name=key)
            val_el = SubElement(data, "value")
            val_el.text = str(value) if value is not None else ""

        gps = building.get("gps_address")
        if gps:
            lat, lon = [x.strip() for x in gps.split(",")]
            point = SubElement(placemark, "Point")
            coords = SubElement(point, "coordinates")
            coords.text = f"{lon},{lat},0"

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "all_buildings.kml"
    indent(kml, space="  ")
    tree = ElementTree(kml)
    tree.write(str(output_path), encoding="utf-8", xml_declaration=True)
    return output_path
