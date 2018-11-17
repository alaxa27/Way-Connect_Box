#!/usr/bin/env python3
from dotenv.main import dotenv_values
import fileinput
import os
import requests
import subprocess

from sign import sign

configFilesLocations = {
    'INTERFACE_IN': [
        '/etc/iptables.ipv4.nat'
    ],
    'INTERFACE_OUT': [
        '/etc/nodogsplash/nodogsplash.conf',
        '/etc/dnsmasq.conf',
        '/etc/iptables.ipv4.nat',
        'interfaces'
    ],
    'PORTAL_HOST': [
        '/etc/nodogsplash/htdocs/splash.html'
    ],
    'ESTABLISHMENT_NAME': [
        '/etc/hostapd/hostapd.conf'
    ]
}

class MissingConfigOnServer(Exception):
    pass


def replace_occurences(key, value, fileLocation):
    with fileinput.FileInput(fileLocation, inplace=True) as file:
    for line in file:
        print(line.replace(f'WC_{key}', value), end='')


def get_current_config():
    path = '/home/pi/env'
    return dotenv_values(path)

    
def copy_default_config():
    subprocess.call('cp -R /home/pi/config/* /etc/')
    

def write_config(config):
    for var in configFilesLocations:
        if var not in config:
            post_box_status(False)
            raise MissingConfigOnServer()

    for varName, fileLocations in configFilesLocations:
        for fileLocation in fileLocations:
            replace_occurences(varName, config[varName], fileLocation)


def post_box_status(state):
    serviceList = ['dhcpd', 'dnsmasq', 'hostapd', 'nodogsplash']
    boxStatus = {}
    for service in serviceList:
        boxStatus[f'{service}_running'] = True
        boxStatus[f'{service}_message'] = 'Default message.'
    boxStatus['internet_connection_active'] = state
    boxStatus['internet_connection_message'] = 'Default message.'
    boxStatus['connected_customers'] = 0

    requests.post(url='http://localhost:5000/boxes/status/', data=boxStatus)


def get_box_config():
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']
    apiHost = 'api.way-connect.com'

    signature = sign(API_KEY, API_SECRET, {})
    headers = {}
    headers['Host'] = apiHost
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    remoteConfig = requests.get(
        url=f'https://{apiHost}/boxes/config/', headers=headers
        )
    return remoteConfig.json()


if __name__=='__main__':
    post_box_status(True)

    currentConfig = get_current_config()
    remoteConfig = get_box_config()

    if remoteConfig != currentConfig:
        copy_default_config()
        try:
            write_config(remoteConfig)
        except MissingConfigOnServer:
            sys.exit(1)
        reboot()
