from dotenv import load_dotenv, main
import fileinput
import os
from pathlib import Path
import requests
import shutil

from utils import sign


class ApplyConfigError(Exception):
    pass


class CopyConfigError(Exception):
    pass


class FetchConfigError(Exception):
    pass


class FetchEstablishmentError(Exception):
    pass


class GetCurrentConfigError(Exception):
    pass


class GetRemoteConfigError(Exception):
    pass


class MissingConfigOnServer(Exception):
    pass


class MissingKeyInConfig(Exception):
    pass


class SaveConfigError(Exception):
    pass


class RemoveFolderError(Exception):
    pass


class WriteConfigError(Exception):
    pass


def apply_config(config, configFiles, configDir, configDestination):
    tmpPath = '/tmp/wayboxconfigdir'

    print('Removing old temporary folder...', end='')
    try:
        remove_folder(tmpPath)
    except RemoveFolderError:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')

    print('Copying config files to temporary dir...', end='')
    try:
        copy_default_config(configDir, tmpPath)
    except CopyConfigError:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')

    print('Writing config in temporary files...', end='')
    try:
        write_config(config, configFiles, tmpPath)
    except WriteConfigError:
        print('FAIL')
        raise ApplyConfigError()
    except MissingConfigOnServer:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')

    print('Copying config files to system config folder...', end='')
    try:
        copy_default_config(tmpPath, configDestination)
    except CopyConfigError:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')


def copy_default_config(fromDir, toDir):
    try:
        shutil.copy_tree(fromDir, toDir)
    except Exception:
        raise CopyConfigError()


def fetch_config(envPath):
    print('Retrieving current config...', end='')
    try:
        currentConfig = get_current_config(envPath)
    except GetCurrentConfigError:
        print('FAIL')
        raise FetchConfigError()
    print('OK')

    print('Retrieving remote config...', end='')
    try:
        remoteConfig = get_remote_config()
    except GetRemoteConfigError:
        print('FAIL')
        raise FetchConfigError()
    print('OK')
    return currentConfig, remoteConfig


def get_config_key(config, key):
    try:
        value = config[key]
    except KeyError as key:
        raise MissingKeyInConfig(f'{key} key is missing in configuration.')
    return value


def get_current_config(configPath):
    return main.dotenv_values(configPath)


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
    except Exception:
        raise FetchConfigError()

    response = remoteConfig.json()

    remoteHost = response['API_HOST']
    try:
        establishmentInfo = requests.get(
            url=f'http://{remoteHost}/customers/establishment/',
            headers=headers
        )
    except Exception:
        raise FetchEstablishmentError()

    response['ESTABLISHMENT_NAME'] = establishmentInfo.json()['name']
    response['API_KEY'] = API_KEY
    response['API_SECRET'] = API_SECRET
    response['NGROK_SUBDOMAIN'] = API_KEY[:8]
    return response


def remove_folder(path):
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError: 
        raise RemoveFolderError()
    except FileNotFoundError:
        pass


def replace_occurences(key, value, fileLocation):
    with fileinput.FileInput(fileLocation, inplace=True) as file:
        for line in file:
            print(line.replace(f'WC_{key}', value), end='')


def save_config(config, configPath):
    try:
        with open(configPath, 'w') as file:
            for key, value in config.items():
                file.write(f'{key}="{value}"\n')
    except Exception:
        raise WriteConfigError()


def write_config(config, configFiles, folder):
    for var in configFiles:
        if var not in config:
            raise MissingConfigOnServer()

    for varName, fileLocations in configFiles.items():
        for fileLocation in fileLocations:
            try:
                replace_occurences(
                    varName,
                    config[varName],
                    f'${folder}{fileLocation}'
                    )
            except Exception:
                raise WriteConfigError()