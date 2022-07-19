import requests
inputs = [input(), input(), input(), input()]
url=inputs[0]
port=inputs[1]
a=inputs[2]
b = inputs[3]
req=requests.get(url=f'{url}:{port}?a={a}&b={b}')
json = req.json()
json =sorted(json)
for d in json:
    print(d)
