import hmac
import hashlib
import json
import requests
import socket
import subprocess
import sys
import traceback


class PutVersionError(Exception):
    pass


class RetrieveServiceStatusError(Exception):
    pass


class ServiceStateError(Exception):
    pass


def deep_replace(object, occurrence, replacement):
    if type(object) is dict:
        return dict_deep_replace(object, occurrence, replacement)
    elif type(object) is list:
        return list_deep_replace(object, occurrence, replacement)
    elif type(object) is str:
        return str_deep_replace(object, occurrence, replacement)
    else:
        return object


def dict_deep_replace(dict, occurrence, replacement):
    for k, v in dict.items():
        dict[k] = deep_replace(v, occurrence, replacement)

    return dict


def list_deep_replace(list, occurrence, replacement):
    for iteratee, item in enumerate(list):
        list[iteratee] = deep_replace(item, occurrence, replacement)

    return list


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


def post_box_status(
    dhcpd_running=True,
    dhcpd_message='Default message.',
    dnsmasq_running=True,
    dnsmasq_message='Default message.',
    hostapd_running=True,
    hostapd_message='Default message.',
    internet_connection_active=True,
    internet_connection_message='Default message.',
    nodogsplash_running=True,
    nodogsplash_message='Default message.',
    update_running=True,
    update_message='Default message.'
):

    boxStatus = {}

    boxStatus['dhcpd_running'] = dhcpd_running
    boxStatus['dhcpd_message'] = dhcpd_message
    boxStatus['dnsmasq_running'] = dnsmasq_running
    boxStatus['dnsmasq_message'] = dnsmasq_message
    boxStatus['hostapd_running'] = hostapd_running
    boxStatus['hostapd_message'] = hostapd_message
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


def post_error_status(type):
    error = {}
    error['error_type'] = type
    error['error_traceback'] = traceback.format_exc()
    post_box_status(
        internet_connection_active=False,
        internet_connection_message=error
        )
    traceback.print_exc()
    sys.exit(1)


def post_service_status():
    services = [
        {
            'from': 'middleware',
            'to': 'dhcpd'
        },
        {
            'from': 'nginx',
            'to': 'dnsmasq'
        },
        {
            'from': 'hostapd',
            'to': 'hostapd',
        },
        {
            'from': 'nodogsplash',
            'to': 'nodogsplash'
        },
        {
            'from': 'ngrok',
            'to': 'update'
        },
    ]

    request = {}
    for service in services:
        status_dict = retrieve_service_status(service['from'])
        status_state = service_state(status_dict)
        request[service['to']] = {
            'running': status_state,
            'message': str(status_dict)
        }
    # Retrieve services status
    post_box_status(
        dhcpd_running=request['dhcpd']['running'],
        dhcpd_message=request['dhcpd']['message'],
        dnsmasq_running=request['dnsmasq']['running'],
        dnsmasq_message=request['dnsmasq']['message'],
        hostapd_running=request['hostapd']['running'],
        hostapd_message=request['hostapd']['message'],
        nodogsplash_running=request['nodogsplash']['running'],
        nodogsplash_message=request['nodogsplash']['message'],
        update_running=request['update']['running'],
        update_message=request['update']['message'],
    )


def put_box_version(commitHash):
    boxVersion = {}
    boxVersion['commit_hash'] = commitHash

    try:
        requests.put(
            url='http://localhost:5000/portal/boxes/version/',
            json=boxVersion
        )
    except Exception:
        raise PutVersionError()


def reboot():
    subprocess.call('/sbin/shutdown -r now', shell=True)


def replace_host(textObject, original, replacement):
    try:
        response_dict = json.loads(textObject)
    except json.decoder.JSONDecodeError:
        return textObject
    response_dict = deep_replace(response_dict, original, replacement)
    response_dict = deep_replace(
        response_dict,
        f'https://{replacement}',
        f'http://{replacement}'
        )
    return json.dumps(response_dict)


def retrieve_service_status(serviceName):
    try:
        key_value = subprocess.check_output(
            ['/bin/systemctl', 'show', serviceName],
            universal_newlines=True).split('\n')
    except subprocess.SubprocessError:
        raise RetrieveServiceStatusError()
    except OSError:
        raise RetrieveServiceStatusError()

    json_dict = {}
    for entry in key_value:
        kv = entry.split("=", 1)
        if len(kv) == 2:
            json_dict[kv[0]] = kv[1]

    return json_dict


def service_state(statusDict):
    try:
        activeState = statusDict['ActiveState']
    except KeyError:
        raise ServiceStateError()
    if activeState == 'active':
        return True
    return False


def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())


def str_deep_replace(str, occurrence, replacement):
    return str.replace(occurrence, replacement)
