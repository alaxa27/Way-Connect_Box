#!/usr/bin/env python3.7
from dotenv import load_dotenv, main
import fileinput
import os
from pathlib import Path
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
        '/etc/dhcpcd.conf'
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


class MissingKeyInConfig(Exception):
    pass


def get_config_key(config, key):
    try:
        value = config[key]
    except KeyError as key:
        raise MissingKeyInConfig()

    return value

def replace_occurences(key, value, fileLocation):
    with fileinput.FileInput(fileLocation, inplace=True) as file:
        for line in file:
            print(line.replace(f'WC_{key}', value), end='')


def get_current_config():
    path = '/home/pi/env'
    return main.dotenv_values(path)

    
def copy_default_config():
    subprocess.call('cp -R /home/pi/Way-Connect_Box/config/* /etc/', shell=True)
    
def reboot():
    subprocess.call('reboot', shell=True)

def apply_config(config):
    for var in configFilesLocations:
        if var not in config:
            raise MissingConfigOnServer()

    for varName, fileLocations in configFilesLocations.items():
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

    res = requests.post(url='http://localhost:5000/boxes/status/', json=boxStatus)


def get_box_config():
    keysPath = Path('/home/pi')
    load_dotenv(dotenv_path=keysPath / 'keys', override=True)
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']
    apiHost = 'wayconnect-staging.herokuapp.com'

    signature = sign(API_KEY, API_SECRET, {})
    headers = {}
    headers['Host'] = apiHost
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    remoteConfig = requests.get(
        url=f'https://{apiHost}/boxes/config/', headers=headers
        )

    response = remoteConfig.json()

    remoteHost = response['API_HOST']
    establishmentInfo = requests.get(
        url=f'https://{remoteHost}/customers/establishment/', headers=headers
        )
    response['ESTABLISHMENT_NAME'] = establishmentInfo.json()['name']
    response['API_KEY'] = API_KEY
    response['API_SECRET'] = API_SECRET
    return response


if __name__=='__main__':
    post_box_status(True)

    currentConfig = get_current_config()
    remoteConfig = get_box_config()

    if remoteConfig != currentConfig:
        copy_default_config()
        try:
            apply_config(remoteConfig)
        except MissingConfigOnServer:
            sys.exit(1)
        reboot()
