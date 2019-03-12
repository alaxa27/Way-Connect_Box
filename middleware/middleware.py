import os
from flask import Flask, request
from flask_cors import CORS
from nameko.exceptions import RemoteError
from nameko.standalone.rpc import ServiceRpcProxy
import requests

from status import post_error_status
from utils import (
    replace_host,
    sign,
    get_ip_from_request
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


NAMEKO_CONFIG = {'AMQP_URI': "amqp://guest:guest@localhost"}


@app.route('/portal/customers/authenticate', methods=['GET'])
def authenticate():
    if STAGE == 'production':
        ip = get_ip_from_request(request)
        with ServiceRpcProxy('ndsctl_service', NAMEKO_CONFIG) as proxy:
            try:
                proxy.auth_client(str(ip))
            except RemoteError:
                post_error_status('ndsctl', exit=False)
                return f'Error authenticating: {ip}', 400
            return 'Authentication Successful.', 200
    return 'Dev auth.', 200

    # params = {
    #     'tok': client['token'],
    #     'redir': 'http://google.com'
    # }
    # url = f'http://192.168.220.2:2050/nodogsplash_auth/?{urlencode(params)}'
    # res = jsonify(url=url)
    # return (res, 200)

@app.route('/portal/box', methods=['GET'])
def box():
    return API_KEY

@app.route('/portal/customers/connect/', methods=['POST'])
def connect():
    ip = get_ip_from_request(request)

    try:
        cacheStatus = request.headers['X-NoCache']
    except KeyError:
        if STAGE == "production":
            with ServiceRpcProxy('ndsctl_service', NAMEKO_CONFIG) as proxy:
                try:
                    connectResult = proxy.get_connect_from_ip(str(ip))
                except RemoteError:
                    post_error_status('ndsctl', exit=False)
                    return f'Error connecting: {ip}', 400
                return connectResult

    return make_signed_request('customers/connect/', request)



@app.route(
    '/portal/',
    methods=['POST', 'GET', 'PATCH', 'PUT'],
    defaults={'path': ''}
    )
@app.route('/portal/<path:path>', methods=['POST', 'GET', 'PATCH', 'PUT'])
def catch_all(path):

    print(request.headers)
    print(path)

    return make_signed_request(path, request)

def make_signed_request(path, request):
    ip = get_ip_from_request(request)
    print(str(ip))

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
    try:
        mac = headers['X-Customer-Mac']
    except KeyError:
        mac = '11:11:11:11:11:11'
        if STAGE == 'production':
            with ServiceRpcProxy('ndsctl_service', NAMEKO_CONFIG) as proxy:
                mac = proxy.get_client_mac(str(ip))
            
    headers['X-Customer-Mac'] = mac
        
    esreq = requests.Request(
        method=request.method,
        url=url, data=request.data,
        params=params,
        headers=headers)
    print(url)
    resp = requests.Session().send(esreq.prepare())
    resp.encoding = 'utf-8'

    resp_text = resp.text
    if STAGE == 'production':
        resp_text = replace_host(resp_text, 'storage.googleapis.com', 'w.zone:5001')

    return (resp_text, resp.status_code, resp.headers.items())


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
