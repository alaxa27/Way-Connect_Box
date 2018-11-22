import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from urllib.parse import urlencode
from utils import (
    sign,
    post_box_status,
    get_ip_from_request,
    get_client_from_ip,
    NdsctlExecutionFailed
)


app = Flask(__name__)
CORS(app)

try:
    STAGE = os.environ['STAGE']
except KeyError:
    STAGE = 'development'

API_HOST = os.environ['API_HOST']
API_URL = 'https://' + API_HOST + '/'
API_KEY = os.environ['API_KEY']
API_SECRET = os.environ['API_SECRET']


@app.route('/portal/customers/authenticate', methods=['GET'])
def authenticate():
    ip = get_ip_from_request(request)
    try:
        client = get_client_from_ip(str(ip))
    except NdsctlExecutionFailed as e:
        post_box_status(
            True,
            nodogsplash_running=False,
            nodogsplash_message=str(e)
            )
        return (f'Error authenticating: {ip}', 400)

    params = {
        'tok': client['token'],
        'redir': 'http://google.com'
    }
    url = f'http://192.168.220.2:2050/nodogsplash_auth/?{urlencode(params)}'
    res = jsonify(url=url)
    return (res, 200)


@app.route(
    '/portal/',
    methods=['POST', 'GET', 'PATCH', 'PUT'],
    defaults={'path': ''}
    )
@app.route('/portal/<path:path>', methods=['POST', 'GET', 'PATCH', 'PUT'])
def catch_all(path):
    ip = get_ip_from_request(request)
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

    esreq = requests.Request(
        method=request.method,
        url=url, data=request.data,
        params=params,
        headers=headers)
    print(url)
    resp = requests.Session().send(esreq.prepare())

    return (resp.text, resp.status_code, resp.headers.items())


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
