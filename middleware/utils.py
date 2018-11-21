import hmac, hashlib, json
import requests
import subprocess


class AuthenticationFailed(Exception):
    pass


class NdsctlExecutionFailed(Exception):
    pass


class KeyMissingInNdsctlOutput(Exception):
    pass


def call_ndsctl(params):
    args = ['sudo', '/usr/bin/ndsctl']
    args += params
    output = subprocess.check_output(args)
        
    return json.loads(output)


def retrieve_client_list(output):
    clients = output['clients']
    clientList =  []
    for clientMac, clientInfo in clients.items():
        client = {}
        client['mac'] = clientMac
        client['ip'] = clientInfo['ip']
        client['token'] = clientInfo['token']
        clientList.append(client)
        
    return clientList


def get_client_from_ip(ip):
    try: 
        ndsctlOutput = call_ndsctl(['json'])
    except OSError as e:
        raise NdsctlExecutionFailed(str(e))        
    except subprocess.SubprocessError as e:
        raise NdsctlExecutionFailed(str(e))

    try:
        clientList = retrieve_client_list(ndsctlOutput)
    except KeyError as e:
        raise KeyMissingInNdsctlOutput(str(e))
        
    for client in clientList:
        if client['ip'] == ip:
            return client
    result = {}
    result['ip'] = ip
    result['mac'] = '22:22:22:22:22:22'
    result['token'] = 'token'
    return result


def authenticate_customer(ip):
    try: 
        call_ndsctl(['auth', ip])
    except OSError as e:
        raise AuthenticationFailed(str(e))        
    except subprocess.SubprocessError as e:
        raise AuthenticationFailed(str(e))


def get_ip_from_request(request):
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip
    

def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())


def post_box_status(
    state,
    update_running=True,
    update_message='Default message.',
    nodogsplash_running=True,
    nodogsplash_message='Default message.'
    ):
    serviceList = ['dhcpd', 'dnsmasq', 'hostapd', 'update']
    boxStatus = {}
    for service in serviceList:
        boxStatus[f'{service}_running'] = True
        boxStatus[f'{service}_message'] = 'Default message.'

    boxStatus['internet_connection_active'] = state
    boxStatus['internet_connection_message'] = 'Default message.'
    boxStatus['nodogsplash_running'] = nodogsplash_running
    boxStatus['nodogsplash_message'] = nodogsplash_message
    boxStatus['update_running'] = update_running
    boxStatus['update_message'] = update_message
    boxStatus['connected_customers'] = 0

    res = requests.post(
        url='http://localhost:5000/portal/boxes/status/',
        json=boxStatus
        )
