import hmac
import hashlib
import json
import requests
import socket
import subprocess


class PutVersionError(Exception):
    pass


def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())


def put_box_version(commitHash):
    boxVersion = {}
    boxVersion['commit_hash'] = commitHash

    try:
        requests.put(
            url='http://localhost:5000/portal/boxes/version/',
            json=boxVersion
        )
    except Exception:
        raise PutVersionError('Error while putting the version to the backend.')


def post_box_status(
    state,
    config_running=True,
    config_message='Default message.',
    internet_connection_active=True,
    internet_connection_message='Default message.',
    update_running=True,
    update_message='Default message.',
    crontab_running=True,
    crontab_message='Default message',
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


def dict_deep_replace(dict, occurrence, replacement):
    for k, v in dict.items():
        dict[k] = deep_replace(v, occurrence, replacement)

    return dict


def list_deep_replace(list, occurrence, replacement):
    for iteratee, item in enumerate(list):
        list[iteratee] = deep_replace(item, occurrence, replacement)

    return list


def str_deep_replace(str, occurrence, replacement):
    return str.replace(occurrence, replacement)


def deep_replace(object, occurrence, replacement):
    if type(object) is dict:
        return dict_deep_replace(object, occurrence, replacement)
    elif type(object) is list:
        return list_deep_replace(object, occurrence, replacement)
    elif type(object) is str:
        return str_deep_replace(object, occurrence, replacement)
    else:
        return object


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


def reboot():
    subprocess.call('/sbin/shutdown -r now', shell=True)
