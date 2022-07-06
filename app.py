import json
import os.path
import h3
from io import BytesIO
from PIL import Image, ImageDraw
from flask import Flask, send_file, jsonify, make_response, request, current_app, Response
from datetime import timedelta
from functools import update_wrapper
import math
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


# C# клас для конвертации яндекс карт в координаты и обратно
# координаты в формате DD.DDDDD
# положение на карте x,y в пикселах от верхнего левого угла на глобальной карте
# то есть чтобы вычислить координаты в конкретном тайле нужно знать его смещение на глобальной карте
# z - zoom увеличение


def YtoLat(y,z): #перевод пиксела ось Y в широту Lat

    a = 6378137.0;
    c1 = 0.00335655146887969;
    c2 = 0.00000657187271079536;
    c3 = 0.00000001764564338702;
    c4 = 0.00000000005328478445;


    mercY = 20037508.342789 - (y * math.pow(2,23 - z)) / 53.5865938;
    g = math.pi / 2 - 2 * math.atan(1 / math.exp(mercY / a));
    zz = g + c1 * math.sin(2 * g) + c2 * math.sin(4 * g) + c3 * math.sin(6 * g) + c4 * math.sin(8 * g);
    return (zz * 180 / math.pi);



def LatToY(lat, z): # перевод широты Lat в координаты пиксела ось Y
    if (lat > 89.5): lat = 89.5; #### newcode
    if (lat < -89.5): lat = -89.5;#### newcode
    rLat = lat * math.pi / 180;
    a = 6378137.0;
    k = 0.0818191908426;
    zz = math.tan(math.pi / 4 + rLat / 2)  / math.pow((math.atan(math.pi / 4 + math.asin(k * math.sin(rLat)) / 2)), k);
    # print(f'(20037508.342789 - {a} * math.log({zz})) * 53.5865938 / math.pow( 2 ,23 - {z});')
    y = (20037508.342789 - a * math.log(zz)) * 53.5865938 / math.pow( 2 ,23 - z);
    return y ;



def XtoLon(x, z): #перевод пиксела ось X в долготу Lon

    lon = 360.0 * x / (256 * math.pow(2, z)) - 180.0;
    if (lon > 180): lon -= 360; #вычисление долготы по пикселу
    return (lon);


def LonToX(lon, z): # перевод долготы Lon в координаты пиксела ось X

    l =  (lon + 180.0)/360.0*(256 * math.pow(2, z));
    return l;
################################################################################3
print(f'y={LatToY(84.733776, 0)}', end=', ')
print(f'x={LonToX(84.587936, 0)}')
print(f'lon={XtoLon(255, 0)}', end=', ')
print(f'lat={YtoLat(255, 0)}')








projections = [{
        'name': 'wgs84Mercator',
        'eccentricity': 0.0818191908426
    }, {
        'name': 'sphericalMercator',
        'eccentricity': 0
    }]
parames = {
    'projection': projections[0]
};
def fromGeoToPixels(lat, long, projection, z):

    x_p, y_p, =0,0
    pixelCoords =0
    tilenumber = []
    rho=0
    pi = math.pi
    beta=0
    phi=0
    theta=0
    e = projection['eccentricity'];

    rho = math.pow(2, z + 8) / 2;
    beta = lat * pi / 180;
    phi = (1 - e * math.sin(beta)) / (1 + e * math.sin(beta));
    theta = math.tan(pi / 4 + beta / 2) * math.pow(phi, e / 2);
    x_p = rho * (1 + long / 180);
    y_p = rho * (1 - math.log(theta) / pi);
    return {'x':x_p, 'y':y_p};

def fromPixelsToTileNumber (x, y):
    return {
        'x':math.floor(x / 256),
        'y':math.floor(y / 256)
    };

############################################################
print(fromGeoToPixels(
    lat=55.733776,
    long=37.587936,
    projection=parames['projection'],
    z=0
))
r_major= 6378137.0; #// Equatorial Radius, WGS84
r_minor=6356752.314245179; #// defined as constant
f=298.257223563;#// 1 / f=(a-b) / a, a = r_major, b = r_minor

def deg2rad(d):
    r = d * (math.pi / 180.0);
    return r;

def rad2deg(r):
    d = r / (math.pi / 180.0);
    return d;

def ll2m(lon, lat): #// lat lon to mercator
    #// lat, lon in rad
    x = r_major * deg2rad(lon);

    if (lat > 89.5): lat = 89.5;
    if (lat < -89.5): lat = -89.5;
    temp = r_minor / r_major;
    es = 1.0 - (temp **2);
    eccent = math.sqrt(es);
    phi = deg2rad(lat);
    sinphi = math.sin(phi);
    con = eccent * sinphi;
    com = .5 * eccent;
    con2 = math.pow((1.0 - con) / (1.0 + con), com);
    ts = math.tan(.5 * (math.pi * 0.5 - phi)) / con2;
    y = 0 - r_major * math.log(ts);
    ret = {'x': x, 'y': y};
    return ret;




def m2ll(x, y): #// mercator to lat lon{
    lon = rad2deg((x / r_major));
    temp = r_minor / r_major;
    e = math.sqrt(1.0 - (temp * temp));
    lat = rad2deg(pj_phi2(math.exp(0 - (y / r_major)), e));
    ret = {'lon': lon, 'lat': lat};
    return ret;



def pj_phi2(ts, e):
    N_ITER = 15;
    HALFPI = math.pi / 2;
    TOL = 0.0000000001;
    eccnth, Phi, con, dphi,i = 0,0,0,0,0
    eccnth = .5 * e;
    Phi = HALFPI - 2. * math.atan(ts);
    i = N_ITER;
    while True:
        con = e * math.sin(Phi);
        dphi = HALFPI - 2. * math.atan(ts * math.pow((1. - con) / (1. + con), eccnth)) - Phi;
        Phi =Phi+ dphi;
        i=i-1
        if not ((abs(dphi) > TOL) and i):break
    return Phi;


############################################################### // usage
print(f'll2m = {ll2m(lon=37.617778, lat=55.751667)}')
print(f'm2ll = {m2ll(x=4187591.891734409, y= 7473789.461896971)}')


geoJson=   {
        "type": "Polygon",
        "coordinates": [
          [
            [
              46.08215332031249,
              61.62989673168073
            ],
            [
              47.35656738281249,
              61.62989673168073
            ],
            [
              47.35656738281249,
              62.04213770379758
            ],
            [
              46.08215332031249,
              62.04213770379758
            ],
            [
              46.08215332031249,
              61.62989673168073
            ]
          ]
        ]
      }

def fromPixelsToTileNumber (x, y):
    return [
        math.floor(x / 256),
        math.floor(y / 256)
    ];



def pointToPixel(point, YmapZoom, x, y):
    ret_x= LonToX(point[0], YmapZoom)-x*256
    ret_y= LatToY(point[1], YmapZoom)-y*256
    return (ret_x,ret_y)

def create_hexagons(geoJson, h3zoom=4, YmapZoom=0, x=0,y=0):
    hexagons = list(h3.polyfill(geoJson, h3zoom))
    polylines = []
    lat = []
    lng = []
    for hex in hexagons:
        polygons = h3.h3_set_to_multi_polygon([hex], geo_json=False)
        # flatten polygons into loops.
        outlines = [loop for polygon in polygons for loop in polygon]
        polyline = [outline + [outline[0]] for outline in outlines][0]
        lat.extend(map(lambda v:v[0],polyline))
        lng.extend(map(lambda v:v[1],polyline))
        polylines.append(polyline)
    polylines=map(lambda pg:list(map(lambda point:pointToPixel(point, YmapZoom,x,y),pg)),polylines)
    return list(polylines)


# print(create_hexagons(geoJson))
def get_png_tile(zoom=1, y=1, x=1):
    rightX=XtoLon(x*256,zoom);
    leftX=XtoLon(x*255+255,zoom);
    bottomY=YtoLat(y*256+255, zoom);
    upY=YtoLat(y*255,zoom);
    lu_p={'lon':leftX, "lat":upY};lu_p_arr=[leftX, upY]
    ru_p={'lon':rightX, "lat":upY};ru_p_arr=[rightX,upY]
    lb_p={'lon':leftX, "lat":bottomY};lb_p_arr=[leftX,bottomY]
    rb_p={'lon':rightX, "lat":bottomY};rb_p_arr=[rightX,bottomY]
    geoJson = {
        "type": "Polygon",
        "coordinates": [
            [
                lu_p_arr,
                ru_p_arr,
                rb_p_arr,
                lb_p_arr,
                lu_p_arr
            ]
        ]
    }

    polygons= create_hexagons(geoJson, h3zoom=2, YmapZoom=zoom, y=y, x=x)
    polygons= polygons+create_hexagons(geoJson, h3zoom=3, YmapZoom=zoom, y=y, x=x)

    img = Image.new('RGBA', (256, 256), (100, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    for plgn in polygons:

        draw.polygon(plgn, fill=(0, 0, 0, 0), outline=(255, 0, 0, 100))
    # draw.ellipse((0, 0, 255, 255), fill=(255, 0, 0, 100))
    # ret= img.tobytes()
    # img.close()
    # return ret
    # img.save('temp.png')
    # return 'temp.png'
    img_io = BytesIO()
    img.save(img_io, "PNG")
    img_io.seek(0)

    return img_io


# @app.route('/tiles/<int:zoom>/<int:x>/<int:y>')
# def tiles(zoom, y, x):
#     filename = '_path_to_tiles\\tiles\\0\\%s\\%s\\%s.png' % (zoom, x, y)
#     png_tile=get_png_tile(zoom, y, x)
#     return send_file(png_tile, mimetype='image/png')

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

    featCollection= {"type": "FeatureCollection",
  "features": [


  ]
        }
    # featCollection['features'].append(geoJson)
    featCollection['features'].append({"type":"Feature","id":0,"geometry":{"type":"Point","coordinates":[35.6894875000,139.6917064000]},"properties":{"balloonContentHeader":"Токио","balloonContentBody":"fff","balloonContentFooter":"fff","clusterCaption":"fff","hintContent":"Токио"}},
)
    featCollection['features'].append({"type":  "Feature","id":4,"geometry":{"type":"Point","coordinates":[35.0,100]},"properties":{"ipAddress":"X.X.X.X","score":"1000"}})


    fc2={
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 123,
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
    ret= f'{callback_id}('+str(json.dumps(fc2))  + ')'
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
