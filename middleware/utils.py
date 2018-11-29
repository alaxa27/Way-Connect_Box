import hmac
import hashlib
import json
import requests
import socket
import subprocess


class AuthenticationFailed(Exception):
    pass


class NdsctlExecutionFailed(Exception):
    pass


class KeyMissingInNdsctlOutput(Exception):
    pass


class CrontabExecutionFailed(Exception):
    pass


class CronWritingError(Exception):
    pass


def call_ndsctl(params):
    args = ['sudo', '/usr/bin/ndsctl']
    args += params
    output = subprocess.check_output(args)

    return json.loads(output)


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


def get_crons(config):
    crons = []
    for key, value in config.items():
        if key.startswith('CRON_'):
            crons.append(value)
    return crons


def write_crons(crons, file):
    with open(file, 'w') as file:
        for cron in crons:
            try:
                file.write(f'{cron}\n')
            except IOError as e:
                raise CronWritingError(str(e))


def save_crons(file):
    try:
        subprocess.check_call(['sudo', '/usr/bin/crontab', file])
    except OSError as e:
        raise CrontabExecutionFailed(str(e))
    except subprocess.SubprocessError as e:
        raise CrontabExecutionFailed(str(e))


def post_box_status(
    state,
    internet_connection_active=True,
    internet_connection_message='Default message.',
    update_running=True,
    update_message='Default message.',
    nodogsplash_running=True,
    nodogsplash_message='Default message.'
):
    serviceList = ['dhcpd', 'dnsmasq', 'hostapd', 'update']
    boxStatus = {}
    for service in serviceList:
        boxStatus[f'{service}_running'] = state
        boxStatus[f'{service}_message'] = 'Default message.'

    boxStatus['internet_connection_active'] = internet_connection_active
    boxStatus['internet_connection_message'] = internet_connection_message
    boxStatus['nodogsplash_running'] = nodogsplash_running
    boxStatus['nodogsplash_message'] = nodogsplash_message
    boxStatus['update_running'] = update_running
    boxStatus['update_message'] = update_message
    boxStatus['connected_customers'] = 0

    requests.post(
        url='http://localhost:5000/portal/boxes/status/',
        json=boxStatus
    )


def is_connected(hostname):
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually
        socket.create_connection((host, 80), 2)
        # reachable
        return True
    except Exception:
        pass
    return False
    