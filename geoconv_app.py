from fastapi import FastAPI, HTTPException
import requests
from fastkml import kml
from typing import List, Dict, Optional
import xmltodict
from pydantic import BaseModel, HttpUrl

class Coordinate(BaseModel):
    longitude: float
    latitude: float

class LineSegment(BaseModel):
    start: Coordinate
    end: Coordinate

class KmlInput(BaseModel):
    url: HttpUrl
    mode: Optional[str] = None

app = FastAPI(docs_url=None)  # Disable the default Swagger UI

@app.get("/geoconv/doc", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
    )

@app.get("/geoconv/kml2json", response_model=Dict[str, List[float]])
async def kml2json(input: KmlInput):
    """
    Convert KML data to longitude/latitude JSON data.

    ## Path
    `GET /geoconv/kml2json/`

    This function will fetch KML data from a URL, parse it, and convert it to longitude/latitude in JSON.

    - **url**: The URL of the KML file.
    - **mode**: The mode for data conversion. Use 'joined' to join intermediate nodes. 
    """

    response = requests.get(input.url)
    #response.raise_for_status()
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not fetch KML data")

    k = kml.KML()
    k.from_string(response.content)

    features = list(k.features())
    placemarks = list(features[0].features())

    line_segments = []
    for placemark in placemarks:
        coords = placemark.geometry.coords
        for i in range(len(coords) - 1):
            line_segments.append(
                LineSegment(
                    start=Coordinate(longitude=coords[i][0], latitude=coords[i][1]),
                    end=Coordinate(longitude=coords[i+1][0], latitude=coords[i+1][1]),
                )
            )

    if input.mode == 'joined':
        return {
            'longitude': [seg.start.longitude for seg in line_segments] + [line_segments[-1].end.longitude],
            'latitude': [seg.start.latitude for seg in line_segments] + [line_segments[-1].end.latitude]
        }
    else:
        return [seg.dict() for seg in line_segments]
