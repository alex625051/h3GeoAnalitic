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
import random

print("Starting server")
# globals:
clusters={}
maxesOfH3Layers = {}
maxValue=0
renderAllHexs = True

redGradient= [
'f9eaee',
'fed6df',
'ffc1ce',
'ffacba',
'ff97a5',
'ff818e',
'ff6b76',
'fe525c',
'f83641',
'ef0324',
]
blueGradient = [
'a8a6f4',
'9995ed',
'8a85e5',
'7b74dd',
'6c63d5',
'5d53cc',
'4e42c3',
'3d31ba',
'2a1eb1',
'0c04a7'
]

ya_h3_zoom = {
    "3":[1,2], "4":[2,3], "5":[3,4], "6":[3,4], "7":[4,5], "8":[6,7], "9":[6,7], "10":[7,8], "11":[8,9], "12":[8,9],
    "13":[9,10], "14":[10,11], "15":[10,11], "16":[11,12], "17":[12,13], "18":[12,13], "19":[13,14], "20":[14,15], "21":[14,15]
}
ya_h3_zoom = {
    "3":[1], "4":[1], "5":[1,2], "6":[2,3], "7":[3,4], "8":[3,4], "9":[4,5], "10":[5,6], "11":[6,7], "12":[6,7],
    "13":[7,8], "14":[8,9], "15":[8,9], "16":[9,10], "17":[10,11], "18":[11,12], "19":[11,12], "20":[12], "21":[12]
}

ya_h3_zoom = {
    "3":[1], "4":[1], "5":[1,2,3], "6":[2,3,4], "7":[3,4,5], "8":[3,4,5], "9":[4,5,6], "10":[5,6,7], "11":[6,7,8], "12":[6,7, 8],
    "13":[7,8,9], "14":[7,8,9,10], "15":[7,8,9,10], "16":[7,8,9,10], "17":[7,8,9,10], "18":[7,8,9,10], "19":[7,8,9,10], "20":[7,8,9,10], "21":[7,8,9,10]
}
degree_1=111 #km

def generataData():
    dataSet = []
    for i in range(0, 1000000):
        dataSet.append({
            "lon": random.uniform(40, 60),
            "lat": random.uniform(40, 60),
            "worker_id": uuid.uuid4()
        })
        dataSet.append({
            "lon": random.uniform(45, 46),
            "lat": random.uniform(45, 46),
            "worker_id": uuid.uuid4()
        })
    return dataSet


def generateClusters(dataSet, H3_zooms):
    clusters={}
    global maxValue
    global maxesOfH3Layers
    for H3_zoom in H3_zooms:
        maxesOfH3Layers[H3_zoom] = {}
        clusters[H3_zoom]={}
        for point in dataSet:
            hxgn=h3.geo_to_h3(lat=point['lat'], lng=point['lon'], resolution=H3_zoom)
            if not hxgn in clusters[H3_zoom]:
                clusters[H3_zoom][hxgn] =1
                # maxesOfH3Layers[H3_zoom]['max'] = maxesOfH3Layers[H3_zoom].get('max', 0) + 1 # От количества полигонов закрашенных
            else:
                clusters[H3_zoom][hxgn] = clusters[H3_zoom][hxgn] + 1
            if clusters[H3_zoom][hxgn] > maxValue: maxValue = clusters[H3_zoom][hxgn]
            maxesOfH3Layers[H3_zoom]['max']=maxesOfH3Layers[H3_zoom].get('max',0)+1 # от количества точек
        maxesOfH3Layers[H3_zoom]['colorW'] = (len(redGradient)-1) / (maxesOfH3Layers[H3_zoom]['max'])


    return clusters






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


def create_hexagons(geoJson, h3zoom, ya_zoom):
    maxesOfH3Layer=0
    hexagons = list(h3.polyfill(geoJson, h3zoom))
    polygons=[]
    for hex in hexagons:
        polygons.append( {"plgn":h3.h3_set_to_multi_polygon([hex], geo_json=False),"hex": hex, "h3zoom": h3zoom})
        maxesOfH3Layer = maxesOfH3Layer + clusters[h3zoom].get(hex,0)
    return polygons, maxesOfH3Layer


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
    for h3_zoom in ya_h3_zoom[ya_zoom]:
        H3LayerPolygons, maxesOfH3Layer = create_hexagons(geoJson, h3_zoom, ya_zoom=ya_zoom)
        polygons = polygons + H3LayerPolygons



    features=[]
    # len_redGradient=len(redGradient)
    # colorW=(len(redGradient)-1)/maxValue
    for polygon in polygons:
        asses = 0
        h3_zoom= polygon['h3zoom']
        fill = False;
        colorW = maxesOfH3Layers[h3_zoom]["colorW"]
        strokeColor = "2222ff";
        strokeWidth = 1
        color = "aaaaff"
        colorI = int(asses * colorW)
        strokeColor = blueGradient[colorI]
        if not polygon['hex'] in clusters[polygon['h3zoom']]:
            fill=False;
            if not renderAllHexs:
                continue
        else:
            asses = clusters[polygon['h3zoom']][polygon['hex']]
            if h3_zoom == ya_h3_zoom[ya_zoom][-1]:
                colorI = int(asses * colorW)
                color= redGradient[colorI]
                fill = True;
            if h3_zoom == ya_h3_zoom[ya_zoom][0]:
                strokeWidth = 5

        features.append({
      "type": "Feature",
      "id": str(uuid.uuid4()), #polygon['hex'],
      "geometry": {
        "coordinates": polygon['plgn'][0],
        "type": "Polygon"
      },
        "properties":{
                # "hintContent": polygon['hex'],
                "hintContent": f'ассайтов: {asses}/{maxesOfH3Layers[h3_zoom]["max"]} <br />H3: {h3_zoom}',
                # "balloonContent": f'ассайтов: {asses}'
            },
            "options":{
                "zIndex": 30+polygon['h3zoom'],

                "fillColor": color,
                # "opacity":0.1,
                "fill":  fill,
                "strokeWidth": strokeWidth,
                "strokeColor": strokeColor,
                "strokeOpacity":1
            }
    })
    fc2={
  "type": "FeatureCollection",
  "features": features
}
    ret= f'{callback_id}('+json.dumps(fc2)  + ')'
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

def main():
    global clusters
    dataSet=generataData()
    clusters = generateClusters(dataSet, range(1,11))
    print("Server started")

if __name__ == '__main__':
    app.run(threadaded = True)
else:
    main()



