# GeoJSON Plotter - Mapflow Building Analysis

A Python tool for extracting building footprints and heights from satellite imagery using the Mapflow API.

## Features

- Process Area of Interest (AOI) using Mapflow API
- Extract building footprints and height data
- Convert results to GeoJSON, JSON, and KML formats
- Transform KML files to GeoJSON

## Prerequisites

- Python 3.8 or higher
- Mapflow API account and credentials

## Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd geojson\ plotter
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

1. Create a .env file in the project root
2. Add your Mapflow API key (as base64 encoded credentials):
   ```
   Mapflow_API_Key=<your_base64_encoded_credentials>
   ```

**To get your API key:**
- Visit [Mapflow API](https://api.mapflow.ai/)
- Sign up for an account
- Generate API credentials
- Encode them as base64: `base64(email:password)`

### 5. Prepare Input Data

Create a GeoJSON file with your Area of Interest (AOI):
- Place it in `aoi_input/` directory
- Name it `input.geojson`
- Must contain a single polygon feature representing your AOI

Example `input.geojson`:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [lon1, lat1],
          [lon2, lat2],
          [lon3, lat3],
          [lon1, lat1]
        ]]
      }
    }
  ]
}
```

## Usage

Run the main script:

```bash
python main.py
```

The script will:
1. Check your remaining Mapflow credits
2. Calculate processing cost for your AOI
3. Prompt you for a project name
4. Process the building data
5. Save results to:
   - `geojson_output/` - Raw Mapflow results (GeoJSON)
   - `finaljson_output/` - Processed results (JSON and KML)

## Library Usage

If you want to reuse this project as a library from another Python project, import the package instead of using the script.

Example:

```python
from geojson_plotter import MapflowClient, mapflow_geojson_to_properties, json_to_kml

client = MapflowClient(key_file="Mapflow_API_key.txt")
geometry = client.load_aoi_geojson("aoi_input/input.geojson")
project_id = "8ebb9d48-299c-47cb-afa9-e61dc1729f71"
response = client.create_processing(project_id=project_id, name="My Project", aoi_polygon=geometry)
client.download_results(response["id"])
mapflow_geojson_to_properties("geojson_output/{response['id']}_results.geojson")
json_to_kml("finaljson_output/all_buildings.json")
```

You can also call the package functions directly without using the command-line script.

## Project Structure

```
.
├── main.py                    # Main entry point
├── mapflow.py                 # Mapflow API client
├── geojson_modifier.py        # GeoJSON processing and property mapping
├── KML_Export.py              # JSON to KML converter
├── kml_to_geojson.py          # KML to GeoJSON converter
├── Mapflow_API_key.txt        # API credentials (keep secret!)
├── aoi_input/                 # Input directory for AOI GeoJSON
├── geojson_output/            # Raw API results
├── finaljson_output/          # Processed output (JSON/KML)
├── KML_Input/                 # KML input files
└── requirements.txt           # Python dependencies
```

## Available Scripts

### `main.py`
Main building analysis workflow using Mapflow API.

### `kml_to_geojson.py`
Convert KML files to GeoJSON format.

Usage:
```bash
python kml_to_geojson.py input.kml [output.geojson]
```

## Output Fields

The processed JSON/KML includes:
- Building properties (type, class, height, area)
- GPS coordinates (latitude, longitude)
- Calculated values (number of storeys, estimated occupancy)
- Shape information

## Troubleshooting

**"API key file not found"**
- Ensure `Mapflow_API_key.txt` exists in the project root
- Check file permissions

**"Insufficient credits"**
- Purchase additional credits on your Mapflow account
- Re-run the script with more credits available

**"Error loading AOI GeoJSON"**
- Verify `aoi_input/input.geojson` exists
- Ensure it contains valid GeoJSON with a single polygon feature

## Requirements

See [requirements.txt](requirements.txt) for full dependency list.

## License

[Add your license here]

## Support

For issues with the Mapflow API, visit: https://mapflow.ai/docs
