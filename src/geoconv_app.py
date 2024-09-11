from fastapi import FastAPI, Query, Body, status #HTTPException, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import requests, base64, json, itertools
from fastkml import kml
from matplotlib import pyplot as plt
from io import BytesIO
from typing import List, Optional #, Dict
#import xmltodict
from pydantic import BaseModel, HttpUrl, Field
from tempfile import NamedTemporaryFile
import uvicorn

class Coordinate(BaseModel):
    longitude: float
    latitude: float

#class LineSegment(BaseModel):
#    start: Coordinate
#    end: Coordinate
# with the format:
#line_segments:
#[{
# start: {
#   longitude:	121.27,
#   latitude:	22.52}
# end: {
#   longitude:	121.552,
#   latitude:	22.675
# }, {start: {....}, end:{...}},.....]

# modify to [{start: [121.27, 22.52], end: [121.552, 22.675]}, {start:[...], end:[...]}, ...]
class LineSegment(BaseModel):
    start: List[float]
    end: List[float]

class KmlResponse(BaseModel):
    longitude: List[float]
    latitude: List[float]
    line_segments: Optional[List[LineSegment]]

def generate_custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="ODB geoconv API",
        version="1.0.0",
        # description="ODB geoconv API schema",
        routes=app.routes,
    )
    openapi_schema["servers"] = [
        {
            "url": "https://api.odb.ntu.edu.tw"
        }
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Geoconv App start...")
    yield
    # below code to execute when app is shutting down
    print("Geoconv App ended")

# https://fastapi.tiangolo.com/advanced/behind-a-proxy/
app = FastAPI(root_path="/geoconv", lifespan=lifespan, docs_url=None)  # Disable the default Swagger UI

@app.get("/geoconv/openapi.json", include_in_schema=False)
async def custom_openapi():
    return JSONResponse(generate_custom_openapi()) #app.openapi()) modify to customize openapi.json

@app.get("/geoconv/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/geoconv/openapi.json", #app.openapi_url
        title= "ODB geoconv tools - Swagger UI", #app.title
    )

@app.get("/geoconv/kml2json", response_model=KmlResponse)
async def kml2json(url: HttpUrl = Query(
    None,
    description="The URL of the KML file",
    examples="https://raw.githubusercontent.com/cywhale/geoconv/main/test/test01.kml"
), append: Optional[str] = Query(
    None,
    description="Optional: append 'line_segments' in JSON which has each line segement start/end coordinates"
)):
    """
    Convert KML data to longitude/latitude JSON data.

    ## Path
    `GET /geoconv/kml2json/`

    This function will fetch KML data from a URL, parse it, and convert it to longitude/latitude in JSON.

    - **url**: The URL of the KML file.
    - **append**: append 'line_segments' in JSON which has each line segement start/end coordinates.
    """
    if url is None:
        raise HTTPException(status_code=400, detail="Must specify valid kml URL")

    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Could not fetch KML data")

    k = kml.KML()
    k.from_string(response.content)
    print(k.to_string(prettyprint=True), flush=True)

    features = list(k.features())
    placemarks = [] #list(features[0].features()) #Not work if kml had <Folder> elements

    def handle_feature(feature):
        if isinstance(feature, kml.Placemark):
            placemarks.append(feature)
        elif hasattr(feature, "features"):
            for subfeature in feature.features():
                handle_feature(subfeature)

    for feature in features:
        handle_feature(feature)

    line_segments = []
    for placemark in placemarks:
        coords = placemark.geometry.coords
        for i in range(len(coords) - 1):
            #line_segments.append(
            #    LineSegment(
            #        start=Coordinate(longitude=coords[i][0], latitude=coords[i][1]),
            #        end=Coordinate(longitude=coords[i+1][0], latitude=coords[i+1][1]),
            #    )
            #)
            start = [float(coords[i][0]), float(coords[i][1])]
            end = [float(coords[i+1][0]), float(coords[i+1][1])]
            line_segments.append(LineSegment(start=start, end=end))


    longitude = []
    latitude = []
    segments_dict = []
    for seg in line_segments:
        segments_dict.append(seg.dict())
        longitude.append(seg.start[0]) #seg.start.longitude)
        latitude.append(seg.start[1])  #seg.start.latitude)

    # add the last end coordinate
    longitude.append(line_segments[-1].end[0]) #.longitude)
    latitude.append(line_segments[-1].end[1])  #.latitude)

    response = {
      'longitude': longitude,
      'latitude': latitude
    }
    if append == 'line_segments':
        response['line_segments'] = segments_dict

    return JSONResponse(content=response)

def zprof2img(zdata):
    try:
        json_resp = requests.get(zdata)
        json_resp.raise_for_status()
        data = json_resp.json()
    except (requests.HTTPError, ValueError, json.JSONDecodeError) as e:
        try:
            data = json.loads(zdata)
        except (ValueError, json.JSONDecodeError):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"Error": "Input zdata must be a valid URL or a JSON string."})

        # Validate the JSON has 'longitude' and 'latitude' keys
        if 'longitude' not in data or 'latitude' not in data or 'z' not in data:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                                content={"Error": "Input zdata must include longitude/latitude/z keys and array of data."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"Error": str(e)})

    # Extract z values and normalize
    z = data["z"]
    #z_min = min(z)
    #z_max = max(z)
    #z_normalized = [(val - z_min) / (z_max - z_min) for val in z]
    plt.figure(figsize=(10, 5))

    if 'distance' in data:
        distances = data["distance"]
        # Calculate cumulative distances
        cumulative_distances = list(itertools.accumulate(distances))
        plt.plot(cumulative_distances, z)
        plt.xlabel("Distance (km)")
    else:
        plt.plot(z)
        plt.xlabel("Index")

    plt.title("Z-profile")
    plt.ylabel("Elevation (m)")

    # Save plot to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)  # Yes, it's required to reset the cursor to the beginning of the buffer.

    # Write the image data to a temporary file
    with NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(buf.read())
        temp_file_name = temp_file.name

    # Return the image as a file response
    return FileResponse(temp_file_name, media_type="image/png")


@app.get("/geoconv/zprofile")
async def zprofile(zdata: str = Query(
    None,
    description="A valid URL for JSON source or a JSON string that contains longitude, latitude, and z keys"
)):
    """
    Get z-profile image from longitude/latitude/z data.

    ## Path
    `GET /geoconv/zprofile/`

    This endpoint returns an image as a binary file response. The image is a PNG file, 
    and it is delivered as a stream of bytes.

    - **zdata**: An URL or JSON string.
    """
    return zprof2img(zdata)

class ZprofBody(BaseModel):
    zdata: str = Field(None, description="A valid URL for JSON source or a JSON string that contains longitude, latitude, and z keys")

@app.post("/geoconv/zprofile")
async def zprof_post(body: ZprofBody = Body(...)):
    """
    POST longitude/latitude/z data to get z-profile image.

    ## Path
    `POST /geoconv/zprofile/`

    This endpoint returns an image as a binary file response. The image is a PNG file, 
    and it is delivered as a stream of bytes.

    - **zdata**: An URL or JSON string.
    """
    return zprof2img(body.zdata)

def main():
    uvicorn.run("src.geoconv_app:app", host="127.0.0.1", port=8015, log_level="info")

if __name__ == "__main__":
    main()
