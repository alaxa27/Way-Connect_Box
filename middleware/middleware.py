import os
from flask import Flask, request
from flask_cors import CORS
from werkzeug.datastructures import ImmutableMultiDict
import requests

from utils import sign, get_client_from_ip

app = Flask(__name__)
CORS(app)

STAGE = os.environ['STAGE']
API_HOST = os.environ['API_HOST']
API_URL = 'https://' + API_HOST + '/'
API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']

@app.route('/portal/', methods=['POST', 'GET', 'PATCH', 'PUT'], defaults={'path': ''})
@app.route('/portal/<path:path>', methods=['POST', 'GET', 'PATCH', 'PUT'])
def catch_all(path):
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    print(str(ip))
    pathSplit = path.split('/')
    if pathSplit[0] == 'customers':
        if pathSplit[1] == 'mac':
            mac = '11:11:11:11:11:11'
            if STAGE == 'production':
                client = get_client_from_ip(str(ip))
                mac = client['mac']
            path = path.replace('mac', mac)

    print(request.headers)
    print(path)
    if path == 'box':
        return API_KEY

    url = API_URL + path

    data = {}
    if request.get_json() is not None:
        data = request.get_json()

    params = {}
    for key, value in request.args.items():
        params[key] = value

    if request.method == 'GET':
        signature = sign(API_KEY, API_SECRET, params)
    else:
        signature = sign(API_KEY, API_SECRET, data)

    headers = {}
    for key, value in request.headers.items():
        headers[key] = value

    headers['Host'] = API_HOST
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    esreq = requests.Request(method=request.method, url=url, data=request.data, params=params, headers=headers)
    print(url)
    resp = requests.Session().send(esreq.prepare())

    return (resp.text, resp.status_code, resp.headers.items())

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
