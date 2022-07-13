import json
import h3
from flask import Flask, send_file, jsonify, make_response, request, current_app, Response
from datetime import timedelta
from functools import update_wrapper
import math
import uuid
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
import random
import pandas as pd
from urllib3._collections import HTTPHeaderDict




@app.route('/', methods=['MEW','POST'])
def rom():
    answers={
    'shit':'Entertainment',
    'money':'Prey',
    'water':'Heaven',
    'fire':'Pillow'
    }
    names=request.headers.get('X-Cat-Variable').split(',')
    resp = Response("Foo bar baz")
    answer=','.join(map(lambda name: answers[name],names))
    resp.headers.add_header('X-Cat-Value', answer)
    print(answer)
    return resp



if __name__ == '__main__':
    app.run(threadaded = True)




