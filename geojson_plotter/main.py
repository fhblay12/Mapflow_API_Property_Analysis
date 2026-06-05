import json
import time
from pathlib import Path

from geojson_plotter import MapflowClient, mapflow_geojson_to_properties, json_to_kml

project_id = "8ebb9d48-299c-47cb-afa9-e61dc1729f71"

def load_aoi_geojson(path: str = "aoi_input/input.geojson") -> dict:
    aoi_path = Path(path)
    if not aoi_path.exists():
        raise FileNotFoundError(f"AOI GeoJSON file not found: {aoi_path}")

    with aoi_path.open("r", encoding="utf-8") as f:
        aoi_data = json.load(f)

    return aoi_data["features"][0]["geometry"]


def mapflow_building_analysis() -> None:
    client = MapflowClient()
    email, credits = client.get_credits()
    print(f"Welcome to the Mapflow API. Using account: {email}")
    print(f"Remaining Credits: {credits}\n")

    try:
        geometry = load_aoi_geojson()
    except Exception as exc:
        print(f"Error loading AOI GeoJSON: {exc}")
        raise

    cost_response = client.calculate_total_cost(aoi_polygon=geometry)
    if isinstance(cost_response, dict):
        estimated_cost = cost_response.get("price") or cost_response.get("credits") or 0
    else:
        estimated_cost = cost_response

    print(f"Estimated Cost: {estimated_cost} credits")

    if credits < estimated_cost:
        print("Insufficient credits to proceed with processing. Acquire more credits and try again.")
        return

    project_name = input("Type in the name of the project for this processing and press Enter: ")
    response = client.create_processing(project_id=project_id, name=project_name, aoi_polygon=geometry)
    print(f"Processing created successfully with ID: {response['id']}")

    print("Waiting for processing to complete...")
    while True:
        status = client.get_processing_status(response["id"])
        if status is None:
            raise RuntimeError("Unable to fetch processing status.")
        if status.get("status") == "OK":
            break
        print(f"Processing is still running... {status.get('percentCompleted')}% completed.")
        time.sleep(10)

    print("Downloading results after processing is complete...")
    result_path = client.download_results(response["id"])

    print("Converting results to properties format...")
    mapflow_geojson_to_properties(str(result_path))

    print("Exporting properties to KML format...")
    json_to_kml("finaljson_output/all_buildings.json")


if __name__ == "__main__":
    mapflow_building_analysis()

