import os
import hmac, hashlib, json
from flask import Flask, request
from flask_cors import CORS
from werkzeug.datastructures import ImmutableMultiDict
import requests
app = Flask(__name__)
CORS(app)

API_HOST = os.environ['API_HOST']
API_URL = 'https://' + API_HOST + '/'
API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']

def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())

@app.route('/', methods=['POST', 'GET'], defaults={'path': ''})
@app.route('/<path:path>', methods=['POST', 'GET'])
def catch_all(path):
    url = API_URL + path
    headers = {}
    for key, value in request.headers.items():
        headers[key] = value

    headers['Host'] = API_HOST
    headers['X-API-Key'] = API_KEY
    if request.get_json() is None:
        data = {}
    else:
        data = request.get_json()
    headers['X-API-Sign'] = sign(API_KEY, API_SECRET, data)

    print(headers['X-API-Sign'])

    params = {}
    for key, value in request.args.items():
        params[key] = value

    if request.method == 'POST':
        response = requests.post(url, data=data, headers=headers)
    elif request.method == 'GET':
        response = requests.get(url, params=params, headers=headers)
    else:
        return '400'
    return response.text

if __name__ == '__main__':
    app.run()
