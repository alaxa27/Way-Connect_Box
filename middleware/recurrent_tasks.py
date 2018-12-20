#!/usr/bin/env python3.7
from dotenv import load_dotenv, main
import fileinput
import git
import os
from pathlib import Path
import requests
import subprocess
import sys

from crontab import apply_crontab
from crontab import ApplyCrontabError
from utils import sign, post_box_status, put_box_version
import utils

homePath = '/home/pi'

configFilesLocations = {
    'INTERFACE_IN': [
        '/etc/iptables.ipv4.nat',
        '/etc/network/interfaces'
    ],
    'INTERFACE_OUT': [
        '/etc/nodogsplash/nodogsplash.conf',
        '/etc/dnsmasq.conf',
        '/etc/iptables.ipv4.nat',
        '/etc/network/interfaces'
    ],
    'PORTAL_HOST': [
        '/etc/nginx/sites-enabled/storage_reverse_proxy.conf',
        '/etc/nginx/sites-enabled/portal_reverse_proxy.conf'
    ],
    'ESTABLISHMENT_NAME': [
        '/etc/hostapd/hostapd.conf'
    ],
    'NDS_CLIENT_FORCE_TIMEOUT': [
        '/etc/nodogsplash/nodogsplash.conf'
    ],
    'NGROK_SUBDOMAIN': [
        '/etc/ngrok.yml'
    ]
}


class ApplyCommitError(Exception):
    pass


class ApplySameCommitException(Exception):
    pass


class BranchDoesNotExist(Exception):
    pass


class FetchConfigError(Exception):
    pass


class FetchEstablishmentError(Exception):
    pass


class HeadAlreadyExists(Exception):
    pass


class MissingConfigOnServer(Exception):
    pass


class MissingKeyInConfig(Exception):
    pass


class RunningUpdateError(Exception):
    pass


class UpdateFetchingError(Exception):
    pass


class WriteConfigError(Exception):
    pass

def get_config_key(config, key):
    try:
        value = config[key]
    except KeyError as key:
        raise MissingKeyInConfig(f'{key} key is missing in configuration.')
    return value


def replace_occurences(key, value, fileLocation):
    with fileinput.FileInput(fileLocation, inplace=True) as file:
        for line in file:
            print(line.replace(f'WC_{key}', value), end='')


def get_current_config(configPath):
    return main.dotenv_values(configPath)


def copy_default_config(fromDir, toDir):
    subprocess.call(f'cp -R {fromDir}/* {toDir}/', shell=True)


def reboot():
    subprocess.call('/sbin/shutdown -r now', shell=True)


def save_config(config, configPath):
    try:
        with open(configPath, 'w') as file:
            for key, value in config.items():
                file.write(f'{key}="{value}"\n')
    except Exception:
        raise UnableToWriteConfig()


def apply_config(config, configFiles):
    for var in configFiles:
        if var not in config:
            raise MissingConfigOnServer()

    for varName, fileLocations in configFiles.items():
        for fileLocation in fileLocations:
            replace_occurences(varName, config[varName], fileLocation)


def get_remote_config():
    keysPath = Path('/home/pi')
    load_dotenv(dotenv_path=keysPath / 'keys', override=True)
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']
    apiHost = 'api.way-connect.com'

    signature = sign(API_KEY, API_SECRET, {})
    headers = {}
    headers['Host'] = apiHost
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    try:
        remoteConfig = requests.get(
            url=f'https://{apiHost}/boxes/config/', headers=headers
        )
    except Exception as e:
        raise FetchConfigError(e)

    response = remoteConfig.json()

    remoteHost = response['API_HOST']
    try:
        establishmentInfo = requests.get(
            url=f'http://{remoteHost}/customers/establishment/',
            headers=headers
        )
    except Exception as e:
        raise FetchEstablishmentError(e)

    response['ESTABLISHMENT_NAME'] = establishmentInfo.json()['name']
    response['API_KEY'] = API_KEY
    response['API_SECRET'] = API_SECRET
    response['NGROK_SUBDOMAIN'] = API_KEY[:8]
    return response


def fetch_config(envPath):
    print('Retrieving current config...', end='')
    try:
        currentConfig = get_current_config(envPath)
    except GetCurrentConfigError as e:
        print('FAIL')
        raise FetchConfigError(e)
    print('OK')

    print('Retrieving remote config...', end='')
    try:
        remoteConfig = get_remote_config()
    except GetRemoteConfigError as e:
        print('FAIL')
        raise FetchConfigError(e)
    print('OK')
    return currentConfig, remoteConfig


if __name__ == '__main__':
    envFile = f'{homePath}/env'
    repoPath = f'{homePath}/Way-Connect_Box'
    cronFile = f'{homePath}/cronjobs'
    configDir = f'{repoPath}/config'
    etcDir = '/etc'

    print('---------------Fetch Config---------------')
    try:
        currentConfig, remoteConfig = fetch_config(envFile)
    except FetchConfigError as e:
        post_box_status(config_running=False, config_message=str(e))
        sys.exit(1)
    print('------------------------------------------')
    print('----------------Run Update----------------')
    try:
        updateStatus = run_update(repoPath, remoteConfig)
    except RunningUpdateError as e:
        post_box_status(update_running=False, update_message=str(e))
        sys.exit(1)
    print('------------------------------------------')

    if currentConfig != remoteConfig or updateStatus:
        print('---------------Apply Config---------------')
        try:
            apply_config(remoteConfig, configFilesLocations)
        except ApplyConfigError as e:
            post_box_status(config_running=False, config_message=str(e))
            sys.exit(1)
        print('------------------------------------------')

        print('--------------Apply Crontab---------------')
        try:
            apply_crontab(remoteConfig, cronFile)
        except ApplyCrontabError as e:
            post_box_status(crontab_running=False, crontab_running=str(e))
            sys.exit(1)
        print('------------------------------------------')

        print('----------------Save Config---------------')
        try:
            save_config(remoteConfig, envFile)
        except SaveConfigError as e:
            post_box_status(config_running=False, config_message=str(e))
            sys.exit(1)
        print('------------------------------------------')
        reboot()

    post_box_status(True)
