from fastapi import FastAPI, Query, HTTPException #, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
import requests
from fastkml import kml
from typing import List #, Optional, Dict
#import xmltodict
from pydantic import BaseModel, HttpUrl

class Coordinate(BaseModel):
    longitude: float
    latitude: float

class LineSegment(BaseModel):
    start: Coordinate
    end: Coordinate

class KmlResponse(BaseModel):
    longitude: List[float]
    latitude: List[float]
    line_segments: List[LineSegment] #Optional[List[LineSegment]]

# https://fastapi.tiangolo.com/advanced/behind-a-proxy/
app = FastAPI(root_path="/geoconv", docs_url=None)  # Disable the default Swagger UI

@app.get("/geoconv/openapi.json", include_in_schema=False)
async def custom_openapi():
    return JSONResponse(app.openapi())

@app.get("/geoconv/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/geoconv/openapi.json", #app.openapi_url
        title=app.title + " - Swagger UI",
    )

@app.get("/geoconv/kml2json", response_model=KmlResponse)
async def kml2json(url: HttpUrl = Query(
    None,
    description="The URL of the KML file",
    example="https://raw.githubusercontent.com/cywhale/geoconv/main/test/test01.kml"
)):
    """
    Convert KML data to longitude/latitude JSON data.

    ## Path
    `GET /geoconv/kml2json/`

    This function will fetch KML data from a URL, parse it, and convert it to longitude/latitude in JSON.

    - **url**: The URL of the KML file.
    """
    if url is None:
        raise HTTPException(status_code=400, detail="Must specify valid kml URL")

    response = requests.get(url)
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

    longitude = []
    latitude = []
    segments_dict = []
    for seg in line_segments:
        segments_dict.append(seg.dict())
        longitude.append(seg.start.longitude)
        latitude.append(seg.start.latitude)

    # add the last end coordinate
    longitude.append(line_segments[-1].end.longitude)
    latitude.append(line_segments[-1].end.latitude)
    return {
        'longitude': longitude, #[seg.start.longitude for seg in line_segments] + [line_segments[-1].end.longitude],
        'latitude': latitude, #[seg.start.latitude for seg in line_segments] + [line_segments[-1].end.latitude],
        'line_segments': segments_dict #[seg.dict() for seg in line_segments]
    }
