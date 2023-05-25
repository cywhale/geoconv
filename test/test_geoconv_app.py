from fastapi.testclient import TestClient
#from starlette.testclient import TestClient
from src.geoconv_app import app

client = TestClient(app) #, root_path='/geoconv')

def test_convert_kml():
    #response = client.post("/geoconv/kml2json/", json={"url": "your-test-kml-file-url", "mode": "joined"})
    response = client.get("/geoconv/kml2json",
                          params={"url": "https://raw.githubusercontent.com/cywhale/geoconv/main/test/test01.kml"})
    assert response.status_code == 200
    # Additional assertions based on expected response...
    assert response.json() == {"longitude":[122.364383,122.474152,122.563969,122.663783],"latitude":[37.824664,37.724322,37.624113,37.523917],"line_segments":[{"start":{"longitude":122.364383,"latitude":37.824664},"end":{"longitude":122.474152,"latitude":37.724322}},{"start":{"longitude":122.474152,"latitude":37.724322},"end":{"longitude":122.563969,"latitude":37.624113}},{"start":{"longitude":122.563969,"latitude":37.624113},"end":{"longitude":122.663783,"latitude":37.523917}}]}
