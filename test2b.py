# from urllib3._collections import HTTPHeaderDict
# import requests
import http.client
import json
import re

pattern = re.compile('[\W\s]')

inputs = ['fire', 'water   ', 'money$%^', 'shit']
inputs = ['water', '    fire', 'shit   ', 'money$%^']

# inputs = [input(), input(), input(), input()]

for i in [0,1,2, 3]:
    inputs[i] = re.sub(pattern, '', inputs[i])
    inputs[i] = inputs[i].replace("_", '').strip()

def send_same_headers(values):
    headerValue = ','.join(values)
    headers = {'X-Cat-Variable': headerValue}

    conn = http.client.HTTPConnection('127.0.0.1:5000', timeout=200)
    conn.request(method='MEW', url="", body='{"foo":"foo"}', headers=headers)
    response = conn.getresponse()
    inheaders = response.getheader('X-Cat-Value')
    inheaders = inheaders.split(',')
    for i in [0, 1]:
        inheaders[i] = re.sub(pattern, '', inheaders[i])
        inheaders[i] = inheaders[i].replace("_", '').strip()
    conn.close()
    return inheaders


prepareAnswers = {}
outputs = ['', '', '', '']
reqs = send_same_headers([inputs[0], inputs[1]])
for req in reqs:
    prepareAnswers[req] = 1
reqs = send_same_headers([inputs[2], inputs[3]])
for req in reqs:
    prepareAnswers[req] = 3

reqs = send_same_headers([inputs[0], inputs[2]])
for req in reqs:
    ind = prepareAnswers[req] - 1
    outputs[ind] = req
    prepareAnswers.pop(req)
for ans in prepareAnswers:
    ind = prepareAnswers[ans]
    outputs[ind] = ans

for ans in outputs:
    print(ans)
