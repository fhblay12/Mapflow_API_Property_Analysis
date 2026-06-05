import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.mapflow.ai/rest"
DEFAULT_KEY_FILE = "Mapflow_API_key.txt"


def read_key(key_file: Optional[str] = None) -> str:
    if key_file is None:
        key_file = DEFAULT_KEY_FILE

    key_path = Path(key_file)
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()

    load_dotenv(dotenv_path=key_path, override=False)
    key = os.getenv("Mapflow_API_Key") or os.getenv("MAPFLOW_API_KEY")
    if key:
        return key.strip()

    raise FileNotFoundError(
        f"Mapflow API key not found. Create '{key_file}' or set MAPFLOW_API_KEY / Mapflow_API_Key."
    )


class MapflowClient:
    def __init__(self, api_key: Optional[str] = None, key_file: Optional[str] = None, base_url: str = BASE_URL) -> None:
        if api_key:
            self.api_key = api_key.strip()
        else:
            self.api_key = read_key(key_file)
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }

    def load_aoi_geojson(self, path: str = "aoi_input/input.geojson") -> Dict[str, Any]:
        aoi_path = Path(path)
        if not aoi_path.exists():
            raise FileNotFoundError(f"AOI GeoJSON file not found: {aoi_path}")

        with aoi_path.open("r", encoding="utf-8") as f:
            aoi_data = json.load(f)

        return aoi_data["features"][0]["geometry"]

    def create_project(self, name: str = "Downtown Mapflow Project", description: str = "Project for processing building data") -> str:
        payload = {
            "name": name,
            "description": description,
        }
        resp = self._post("/projects", payload)
        return resp["id"]

    def get_processing_history(self, page: int = 1, per_page: int = 50, status_filter: str = "status=OK") -> Dict[str, Any]:
        payload = {
            "page": page,
            "perPage": per_page,
            "sort": "created:desc",
            "filter": status_filter,
        }
        return self._post("/processings/stats", payload)

    def get_credits(self) -> Tuple[str, int]:
        resp = self._get("/user/status")
        return resp["email"], resp["remainingCredits"]

    def get_processing_status(self, processing_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"/processings/{processing_id}/v2")

    def calculate_total_cost(
        self,
        provider_name: str = "Mapbox",
        wd_id: str = "8cb13006-a299-4df6-b47d-91bd63de947f",
        area_sq_km: float = 1.5,
        aoi_polygon: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        blocks = [
            {"name": "Classification", "enabled": True},
            {"name": "Simplification", "enabled": True},
            {"name": "Heights", "enabled": True},
        ]
        source_params = {"dataProvider": {"providerName": provider_name, "zoom": 18}}

        payload: Dict[str, Any] = {
            "wdId": wd_id,
            "params": {"sourceParams": source_params},
            "blocks": blocks,
        }
        if aoi_polygon is not None:
            payload["geometry"] = aoi_polygon
        else:
            payload["areaSqKm"] = area_sq_km

        return self._post("/processing/cost/v2", payload)

    def create_processing(
        self,
        project_id: str,
        name: str = "Building Analysis",
        provider_name: str = "Mapbox",
        wd_name: str = "🏠 Buildings",
        area_sq_km: float = 1.5,
        aoi_polygon: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_params = {"dataProvider": {"providerName": provider_name, "zoom": 18}}
        payload: Dict[str, Any] = {
            "name": name,
            "projectId": project_id,
            "wdName": wd_name,
            "params": {"sourceParams": source_params},
            "blocks": [
                {"name": "Classification", "enabled": True},
                {"name": "Simplification", "enabled": True},
                {"name": "Heights", "enabled": True},
            ],
        }
        if aoi_polygon is not None:
            payload["geometry"] = aoi_polygon
        else:
            payload["areaSqKm"] = area_sq_km

        return self._post("/processings", payload)

    def download_results(self, processing_id: str, output_dir: str = "geojson_output") -> Path:
        output_path = Path(output_dir) / f"{processing_id}_results.geojson"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(f"{self.base_url}/processings/{processing_id}/result", headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download results: {response.status_code} {response.text}")

        output_path.write_bytes(response.content)
        return output_path

    def _get(self, path: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}{path}", headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(f"{self.base_url}{path}", headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
