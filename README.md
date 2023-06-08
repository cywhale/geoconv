# geoconv

  1. Convert KML data to longitude/latitude JSON data.
  2. Generate a z-profile image from GEBCO API.

#### Usage

```
project/
├─ src/
│  ├─ __init__.py
│  ├─ geoconv_app.py
├─ test/
│  ├─ test_xxx.py
├─ pytest.ini
├─ setup.py


pip install -e .
# testing run on e.g. port 8000
gunicorn src.geoconv_app:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
pytest

# production mode
pm2 start ./conf/ecosystem.config.js

```

#### Swagger API doc

/geoconv/swagger
