import json
import os
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

def json_to_kml(json_path: str, output_dir: str = "finaljson_output") -> str:
    
    with open(json_path, "r") as f:
        buildings = json.load(f)

    # KML root structure
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, "Document")
    name = SubElement(document, "name")
    name.text = "Buildings"

    for i, building in enumerate(buildings):
        placemark = SubElement(document, "Placemark")

        # Name
        pm_name = SubElement(placemark, "name")
        pm_name.text = f"Building {i+1}"

        # Description — all property fields as key: value
        desc = SubElement(placemark, "description")
        desc.text = "\n".join(
            f"{k}: {v}" for k, v in building.items() if v is not None
        )

        # Extended data — each field as a Data element
        extended = SubElement(placemark, "ExtendedData")
        for key, value in building.items():
            data = SubElement(extended, "Data", name=key)
            val_el = SubElement(data, "value")
            val_el.text = str(value) if value is not None else ""

        # Point geometry from gps_address
        gps = building.get("gps_address")
        if gps:
            lat, lon = [x.strip() for x in gps.split(",")]
            point = SubElement(placemark, "Point")
            coords = SubElement(point, "coordinates")
            coords.text = f"{lon},{lat},0"

    # Write to file
    os.makedirs(output_dir, exist_ok=True)
    indent(kml, space="  ")
    tree = ElementTree(kml)
    output_path = os.path.join(output_dir, "all_buildings.kml")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    print(f"KML exported to '{output_path}'")
    return output_path


