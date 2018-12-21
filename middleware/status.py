import requests
import traceback
import subprocess
import sys


class PostBoxStatusError(Exception):
    pass


class PostServiceStatusError(Exception):
    pass


class RetrieveServiceStatusError(Exception):
    pass


class ServiceStateError(Exception):
    pass


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

    try:
        requests.post(
            url='http://localhost:5000/portal/boxes/status/',
            json=boxStatus
        )
    except requests.RequestException:
        raise PostBoxStatusError(Exception)


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
    print('Retrieving statuses...', end='')
    for service in services:
        try:
            status_dict = retrieve_service_status(service['from'])
        except RetrieveServiceStatusError:
            print('FAIL')
            raise PostServiceStatusError()
        status_state = service_state(status_dict)
        if status_state:
            status_dict = {}
        request[service['to']] = {
            'running': status_state,
            'message': str(status_dict)
        }
    print('OK')
    # Retrieve services status
    print('Posting box status service...', end='')
    try:
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
    except PostBoxStatusError:
        print('FAIL')
        raise PostServiceStatusError()
    print('OK')


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
