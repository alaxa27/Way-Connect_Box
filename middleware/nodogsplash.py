import json
import subprocess


class AuthenticationFailed(Exception):
    pass


class NdsctlExecutionFailed(Exception):
    pass


class KeyMissingInNdsctlOutput(Exception):
    pass


def authenticate_customer(ip):
    try:
        call_ndsctl(['auth', ip])
    except OSError:
        raise AuthenticationFailed()
    except subprocess.SubprocessError:
        raise AuthenticationFailed()


def call_ndsctl(params):
    args = ['sudo', '/usr/bin/ndsctl']
    args += params
    output = subprocess.check_output(args)

    return json.loads(output)


def get_client_from_ip(ip):
    try:
        ndsctlOutput = call_ndsctl(['json'])
    except OSError:
        raise NdsctlExecutionFailed()
    except subprocess.SubprocessError:
        raise NdsctlExecutionFailed()

    try:
        clientList = retrieve_client_list(ndsctlOutput)
    except KeyError:
        raise KeyMissingInNdsctlOutput()

    for client in clientList:
        if client['ip'] == ip:
            return client
    result = {}
    result['ip'] = ip
    result['mac'] = '22:22:22:22:22:22'
    result['token'] = 'token'
    return result


def get_ip_from_request(request):
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip


def retrieve_client_list(output):
    clients = output['clients']
    clientList = []
    for clientMac, clientInfo in clients.items():
        client = {}
        client['mac'] = clientMac
        client['ip'] = clientInfo['ip']
        client['token'] = clientInfo['token']
        clientList.append(client)

    return clientList
