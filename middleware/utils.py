import hmac
import hashlib
import json
import socket
import subprocess


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


def get_ip_from_request(request):
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip


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


def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())


def str_deep_replace(str, occurrence, replacement):
    return str.replace(occurrence, replacement)
