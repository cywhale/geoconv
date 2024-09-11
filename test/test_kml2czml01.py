from fastkml import kml
import requests
from datetime import datetime, timedelta
from typing import List

def getKML(url):
    response = requests.get(url)
    if response.status_code != 200:
        print("Could not fetch KML data")

    #k = kml.KML()
    #k.from_string(response.content)
    return response.content

def kml2czml(kml_str: str, start_time: str, end_time: str, time_step: int = 14000) -> List[dict]:
    # Parse KML
    k_obj = kml.KML()
    k_obj.from_string(kml_str)

    features = list(k_obj.features())
    placemarks = list(features[0].features())

    # Base CZML
    czml = [
        {
            "id": "document",
            "name": "CZML movement Dynamic",
            "version": "1.0",
            "clock": {
                "interval": f"{start_time}/{end_time}",
                "currentTime": start_time,
                "multiplier": 10000,
                "range": "LOOP_STOP",
                "step": "SYSTEM_CLOCK_MULTIPLIER"
            }
        }
    ]

    # Convert KML segments to CZML format
    for idx, placemark in enumerate(placemarks):
        coords = placemark.geometry.coords
        cartographicDegrees = []

        current_time = datetime.fromisoformat(start_time)

        for coord_pair in coords:
            cartographicDegrees.extend([
                (current_time - datetime.fromisoformat(start_time)).total_seconds(),
                coord_pair[0],
                coord_pair[1],
                time_step
            ])
            current_time += timedelta(seconds=time_step)

        segment = {
            "id": f"Line-Segment-{idx+1}",
            "availability": f"{start_time}/{end_time}",
            "position": {
                "epoch": start_time,
                "cartographicDegrees": cartographicDegrees
            },
            "billboard": {
              "image":"data:image/png;base64,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",
              "scale": 1,
            },
            #"point": {
            #    "color": {"rgba": [255, 255, 255, 128]},
            #    "outlineColor": {"rgba": [255, 0, 0, 128]},
            #    "outlineWidth": 3,
            #    "pixelSize": 15
            #},
            "path": {
                "resolution": 1,
                "leadTime": 0,
                "trailTime": 172800,
                "material": {
                    "solidColor": {
                        "color": {"rgba": [0, 127, 255, 128]}
                    }
                },
                "width": 2
            },
            "polyline": {
                "show": [{
                    "interval": f"{start_time}/{end_time}",
                    "boolean": True
                }],
                "width": 1,
                "material": {
                    "solidColor": {
                        "color": {"rgba": [0, 255, 255, 255]}
                    }
                },
                "followSurface": False,
                "positions": {
                    "references": [f"Line-Segment-{idx+1}#position"]
                }
            }
        }
        czml.append(segment)

    return czml


url = "https://raw.githubusercontent.com/cywhale/geoconv/main/test/test01.kml"
k1 = getKML(url)
start_time = "2010-02-02T00:00:00Z"
end_time = "2010-02-03T23:59:59Z"

result = kml2czml(k1, start_time, end_time)
print(result)