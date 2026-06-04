import json
import time
from mapflow import calculate_total_cost, create_processing, download_results, get_processing_status, get_credits
from geojson_modifier import mapflow_geojson_to_properties
from KML_Export import json_to_kml


project_id = "8ebb9d48-299c-47cb-afa9-e61dc1729f71"

print(
        "Welcome to the mapflow API. Save the geojson file of the area you want to process as "
        "'input.geojson' in the directory aoi_input. The file should contain a single polygon "
        "feature representing the area of interest (AOI).\n"
        "The processing will extract building footprints and heights within the AOI. After running "
        "this script, the results will be saved in the 'geojson_output' directory as a GeoJSON file "
        "containing the extracted building data.\n"
        "The estimated cost will be displayed based on the AOI size. You can acquire more credits if "
        "needed and run the script again to proceed with processing.\n"
    )
def mapflow_building_analysis():
    credits = get_credits()
    
    print(f"Remaining Credits: {credits[1]}\n")
    geometry = None

    try:
        with open("aoi_input/input.geojson", "r", encoding="utf-8") as f:
            aoi_data = json.load(f)
            geometry = aoi_data["features"][0]["geometry"]
    except Exception as e:
        print(f"Error loading AOI GeoJSON: {e}")
        exit(1)

    calculate_response = calculate_total_cost(aoiPolygon=geometry)
    print(f"Estimated Cost: {calculate_response} credits")

    if credits[1] < calculate_response:
        print("Insufficient credits to proceed with processing. Please acquire more credits and try again.")
        exit(1)

    project_name = input("Type in the name of the project you want to create or use for this processing and press Enter: ")
    response = create_processing(projectId=project_id, aoiPolygon=geometry, name=project_name)
    if response:
        print(f"Processing created successfully with ID: {response['id']}")
        print("Waiting for processing to complete...")
        while True:
            status = get_processing_status(response['id'])
            if status is None:
                print("Unable to fetch processing status. Aborting.")
                exit(1)
            if status["status"] == "OK":
                break
            print(f"Processing is still running... {status['percentCompleted']}% completed.")
            time.sleep(10)

        print("Downloading results after processing is complete...")
        download_results(response['id'])
        print("Converting results to properties format...")
        mapflow_geojson_to_properties(f"geojson_output/{response['id']}_results.geojson")
        print("Exporting properties to KML format...")
        json_to_kml("finaljson_output/all_buildings.json")

