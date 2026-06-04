import json
import os
import requests
from dotenv import load_dotenv

BASE_URL = "https://api.mapflow.ai/rest"
KEY_FILE = "Mapflow_API_key.txt"

def read_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"API key file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

try:
    key = read_key(KEY_FILE)
except Exception as e:
        print(e)

headers = {
        "Authorization": f"Basic {key}",
        "Content-Type": "application/json"
    }

def create_project(name="Downtown Mapflow Project", description="Project for processing downtown building data"):
    payload = {
        "name": name,
        "description": description
    }
    try:
        resp = requests.post(f"{BASE_URL}/projects", headers=headers, json=payload).json()
    except Exception as e:
        print(f"Error creating project: {e}")
    return resp["id"]

def get_processing_history():
    payload = {
            
            "page": 1,
            "perPage": 50,
            "sort": "created:desc",
            "filter": "status=OK"
        }
    try:
        resp = requests.post(f"{BASE_URL}/processings/stats", headers=headers, json=payload).json()
    except Exception as e:        
        print(f"Error fetching processing history: {e}")
    return resp

def get_credits():
    try:
        resp = requests.get(f"{BASE_URL}/user/status", headers=headers).json()
    except Exception as e:
        print(f"Error fetching credit information: {e}")
    #print(resp.status_code)
    #print(resp.text)
    return resp["email"], resp["remainingCredits"]

def get_processing_status(processing_id):
    try:
        resp = requests.get(f"{BASE_URL}/processings/{processing_id}/v2", headers=headers).json()
    except Exception as e:
        print(f"Error fetching processing status: {e}")
        return None
    return resp

def calculate_total_cost(providerName="Mapbox", wdId="8cb13006-a299-4df6-b47d-91bd63de947f", areaSqKm=1.5, aoiPolygon=None):
    
    blocks = [
        {"name": "Classification", "enabled": True},
        {"name": "Simplification", "enabled": True},
        {"name": "Heights",        "enabled": True}
    ]

    source_params = {
        "dataProvider": {
            "providerName": providerName,
            "zoom": 18
        }
    }

    if aoiPolygon:
        payload = {
            "wdId": wdId,
            "geometry": aoiPolygon,
            "params": {"sourceParams": source_params},
            "blocks": blocks
        }
    else:
        payload = {
            "wdId": wdId,
            "areaSqKm": areaSqKm,
            "params": {"sourceParams": source_params},
            "blocks": blocks
        }

    try:
        resp = requests.post(f"{BASE_URL}/processing/cost/v2", headers=headers, json=payload).json()
    except Exception as e:
        print(f"Error calculating total cost: {e}")
        return None

    return resp

def create_processing(projectId="8cb13006-a299-4df6-b47d-91bd63de947f", providerName="Mapbox", areaSqKm=1.5, aoiPolygon=None, name="Building Analysis", wdName="🏠 Buildings"):
    
    source_params = json.dumps({
        "dataProvider": {
            "providerName": providerName,
            "zoom": 18
        }
    })

    if aoiPolygon:
        payload = {
            "name": name,
            "projectId": projectId,
            "wdName": "🏠 Buildings",
            "geometry": aoiPolygon,
            "params": {
                "sourceParams": source_params
            },
            "blocks": [
                {"name": "Classification", "enabled": True},
                {"name": "Simplification", "enabled": True},
                {"name": "Heights",        "enabled": True}
            ]
        }
    else:
        payload = {
            "name": "Building Analysis",
            "projectId": projectId,
            "wdName": "🏠 Buildings",
            "areaSqKm": areaSqKm,
            "params": {
                "sourceParams": source_params
            },
            "blocks": [
                {"name": "Classification", "enabled": True},
                {"name": "Simplification", "enabled": True},
                {"name": "Heights",        "enabled": True}
            ]
        }

    try:
        resp = requests.post(f"{BASE_URL}/processings", headers=headers, json=payload).json()
    except Exception as e:
        print(f"Error creating processing: {e}")
        return None

    return resp

def download_results(processingId):
    try:
        resp = requests.get(f"{BASE_URL}/processings/{processingId}/result", headers=headers)
        if resp.status_code == 200:
            with open(f"geojson_output/{processingId}_results.geojson", "wb") as f:
                f.write(resp.content)
            print(f"Results downloaded successfully: geojson_output/{processingId}_results.geojson")
        else:
            print(f"Failed to download results: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error downloading results: {e}")

aoi_polygon = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "accra_square_aoi"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-0.2250, 5.5400],
                        [-0.2250, 5.5600],
                        [-0.2050, 5.5600],
                        [-0.2050, 5.5400],
                        [-0.2250, 5.5400]
                    ]
                ]
            }
        }
    ]
}



