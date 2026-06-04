import datetime
import json
import os

def mapflow_geojson_to_properties(geojson_path: str, output_dir: str = "finaljson_output") -> list[dict]:
    with open(geojson_path, "r") as f:
        geojson = json.load(f)

    
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        coords = geometry.get("coordinates", [[]])[0]
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            gps_address = f"{sum(lats)/len(lats):.6f}, {sum(lons)/len(lons):.6f}"
        else:
            gps_address = None

        height = props.get("building_height")
        shape_type = props.get("shape_type", "")
        class_name = props.get("class_name", "")
        area = props.get("area")

        property_dict = {
            "owner_id":                  None,
            "ratepayer_id":              None,
            "created_by":                None,
            "property_code":             None,
            "property_use":              class_name or "unknown",
            "prop_class":                str(props.get("class_id")) if props.get("class_id") else None,
            "serial_no":                 None,
            "location":                  None,
            "population_density":        None,
            "street_name":               None,
            "landmark":                  None,
            "gps_address":               gps_address,
            "no_of_people":              0,
            "no_of_bedrooms":            None,
            "no_of_washrooms":           0,
            "no_of_otherrooms":          0,
            "building_type":             {"DYNAMIC_GRID": "flat_apartment"}.get(shape_type, "detached"),
            "building height in m":           height,
            "building area in m^2":             area,
            "no_of_storeys":             str(round(height / 3)) if height else None,
            "electoral_area":            None,
            "town":                      None,
            "community":                 None,
            "ownership_type":            None,
            "permit_status":             None,
            "sanitation_facility_avail": None,
            "sources_of_water":          None,
            "waste_disposal_method":     None,
            "parcel_no":                 None,
            "house_no":                  None,
            "acct_no":                   None,
            "division_no":               None,
            "rating_zone":               None,
            "rateable_value":            None,
            "lvd_val_no":                None,
        }

        results.append(property_dict)

    combined_path = os.path.abspath(os.path.join(output_dir, "all_buildings.json"))
    temp_path = combined_path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    try:
        os.replace(temp_path, combined_path)
        output_path = combined_path
    except PermissionError:
        fallback_path = os.path.abspath(
            os.path.join(
                output_dir,
                f"all_buildings_{datetime.datetime.now():%Y%m%d_%H%M%S}.json",
            )
        )
        os.replace(temp_path, fallback_path)
        output_path = fallback_path
        print(
            f"Warning: could not overwrite '{combined_path}' because it is locked. "
            f"Saved output to '{output_path}' instead."
        )

    print(f"Exported {len(results)} buildings to '{output_path}'")
    return results

if __name__ == "__main__":
    mapflow_geojson_to_properties(
        "geojson_output/e3b894d2-78ec-4348-93a8-4a74a7063b39_results.geojson"
    )

