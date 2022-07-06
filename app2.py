import json
import os.path
import h3
from io import BytesIO
from PIL import Image, ImageDraw
from flask import Flask, send_file, jsonify, make_response, request, current_app, Response
from datetime import timedelta
from functools import update_wrapper
import math
import uuid
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator




def fromPixelsToTileNumber (x, y):
    return {
        'x':math.floor(x / 256),
        'y':math.floor(y / 256)
    };


def create_hexagons(geoJson, h3zoom, YmapZoom):
    hexagons = list(h3.polyfill(geoJson, h3zoom))
    polygons=[]
    for hex in hexagons:
        polygons.append( h3.h3_set_to_multi_polygon([hex], geo_json=False))
    return polygons


@app.route('/rom/<path:resp_string>')
@crossdomain(origin="*")
def rom(resp_string):
    callback_id = request.args.get('callback')
    string_arr=resp_string.split('/')
    ya_zoom = string_arr[1]
    coords=string_arr[0].split(',')
    coords=list(map(lambda x: float(x),coords))

    lu_p_arr=[coords[0], coords[1]]
    ru_p_arr=[coords[2],coords[1]]
    rb_p_arr=[coords[2],coords[3]]
    lb_p_arr=[coords[0],coords[3]]
    coordinates =  [
            [
                lu_p_arr,
                ru_p_arr,
                rb_p_arr,
                lb_p_arr,
                lu_p_arr
            ]
        ]

    geoJson = {
        "type": "Polygon",
        "coordinates": coordinates
    }
    polygons=[]
    polygons=polygons+create_hexagons(geoJson, h3zoom=2, ya_zoom=2)
    features=[]
    for polygon in polygons:
        features.append({
      "type": "Feature",
      "id": str(uuid.uuid4()),
      "geometry": {
        "coordinates": polygon,
        "type": "Polygon"
      },
      "properties": {
        "name": "Многоугольник 1"
      }
    })

    fc2={
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": str(uuid.uuid4()),
      "geometry": {
        "coordinates": coordinates,
        "type": "Polygon"
      },
      "properties": {
        "name": "Многоугольник 1"
      }
    }

  ]
}
    ret= f'{callback_id}('+json.dumps(fc2)  + ')'
    print(ret)
    response = Response(ret, mimetype='text/xml')
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Max-Age', '1000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Content-type', 'text/xml')
    return response


@app.route('/run/')
def run_it():
    return send_file('index2.html')


if __name__ == '__main__':
    app.run(threadaded = True)
