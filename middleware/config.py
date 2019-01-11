from dotenv import load_dotenv, main
import fileinput
import os
from pathlib import Path
import requests
import shutil
import subprocess

import utils


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


class GetListFromConfigError(Exception):
    pass


class GetRemoteConfigError(Exception):
    pass


class MissingConfigOnServer(Exception):
    pass


class MissingKeyInConfig(Exception):
    pass


class SaveConfigError(Exception):
    pass


class ReloadDaemonsError(Exception):
    pass


class RestartServicesError(Exception):
    pass


class RestartUpdatedServicesError(Exception):
    pass


class RemoveFolderError(Exception):
    pass


class WriteConfigError(Exception):
    pass


def apply_config(config, currentConfig, configDir, configDestination): # noqa:C901
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

    print('Generating config files list...', end='')
    try:
        configFiles = get_list_from_config(config, 'FILES')
    except GetListFromConfigError:
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

    print('Reload daemons...', end='')
    try:
        reload_daemons()
    except ReloadDaemonsError:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')

    print('Generating config services list...', end='')
    try:
        configServices = get_list_from_config(config, 'SERVICES')
    except GetListFromConfigError:
        print('FAIL')
        raise ApplyConfigError
    print('OK')

    print('Restarting updated services...', end='')
    try:
        restart_updated_services(config, currentConfig, configServices)
    except RestartUpdatedServicesError:
        print('FAIL')
        raise ApplyConfigError()
    print('OK')


def copy_default_config(fromDir, toDir):
    try:
        shutil.copytree(fromDir, toDir)
    except FileExistsError:
        try:
            subprocess.call(f'cp -R {fromDir}/* {toDir}/', shell=True)
        except OSError:
            raise CopyConfigError()
        except subprocess.SubprocessError:
            raise CopyConfigError()
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


def get_list_from_config(config, occurence):
    result = {}
    for k, v in config.items():
        splitKey = k.split('_')
        if splitKey[0] == occurence:
            try:
                key = '_'.join(splitKey[1:])
            except IndexError:
                raise GetListFromConfigError(f'{occurence}: {k}')
            value = v.split(';')
            result[key] = value
    return result


def get_current_config(configPath):
    return main.dotenv_values(configPath)


def get_remote_config():
    keysPath = Path('/home/pi')
    load_dotenv(dotenv_path=keysPath / 'keys', override=True)
    API_KEY = os.environ['API_KEY']
    API_SECRET = os.environ['API_SECRET']
    apiHost = 'api.way-connect.com'

    signature = utils.sign(API_KEY, API_SECRET, {})
    headers = {}
    headers['Host'] = apiHost
    headers['X-API-Key'] = API_KEY
    headers['X-API-Sign'] = signature

    try:
        remoteConfig = requests.get(
            url=f'https://{apiHost}/boxes/config/', headers=headers
        )
        remoteConfig.raise_for_status()
    except requests.HTTPError:
        raise FetchConfigError()

    response = remoteConfig.json()

    remoteHost = response['API_HOST']
    try:
        establishmentInfo = requests.get(
            url=f'http://{remoteHost}/customers/establishment/',
            headers=headers
        )
        establishmentInfo.raise_for_status()
    except requests.HTTPError:
        raise FetchEstablishmentError()

    response['ESTABLISHMENT_NAME'] = establishmentInfo.json()['name']
    response['API_KEY'] = API_KEY
    response['API_SECRET'] = API_SECRET
    response['NGROK_SUBDOMAIN'] = API_KEY[:8]
    return response


def reload_daemons():
    try:
        subprocess.call('/bin/systemctl daemon-reload', shell=True)
    except subprocess.SubprocessError:
        raise ReloadDaemonsError()
    except OSError:
        raise ReloadDaemonsError()


def remove_folder(path):
    try:
        shutil.rmtree(path, ignore_errors=True)
    except FileNotFoundError:
        pass
    except OSError:
        raise RemoveFolderError()


def restart_services(services):
    for service in services:
        if service == 'monit':
            try:
                subprocess.call(['monit', 'reload'])
            except subprocess.SubprocessError:
                raise RestartServicesError(f'monit reload')
        if service == 'reboot':
            utils.reboot()
        try:
            subprocess.call(['systemctl', 'restart', service])
        except subprocess.SubprocessError:
            raise RestartServicesError(service)


def restart_updated_services(remote, current, configServices):
    for k, services in configServices.items():
        try:
            remoteValue = get_config_key(remote, k)
        except MissingKeyInConfig:
            raise RestartUpdatedServicesError()

        try:
            currentValue = get_config_key(current, k)
        except MissingKeyInConfig:
            try:
                restart_services(services)
            except RestartServicesError:
                raise RestartUpdatedServicesError()
            continue

        if currentValue != remoteValue:
            try:
                restart_services(services)
            except RestartServicesError:
                raise RestartUpdatedServicesError()


def replace_occurence(string, config):
    for key, val in config.items():
        string = string.replace(f'WC_{key}', config[key])
    return string


def replace_occurences(key, value, fileLocation):
    with fileinput.FileInput(fileLocation, inplace=True) as file:
        for line in file:
            print(line.replace(f'WC_{key}', value), end='')


def save_config(config, configPath):
    print('Saving config...', end='')
    try:
        with open(configPath, 'w') as file:
            for key, value in config.items():
                file.write(f'{key}="{value}"\n')
    except IOError:
        print('FAIL')
        raise WriteConfigError()
    except OSError:
        print('FAIL')
        raise WriteConfigError()
    print('OK')


def write_config(config, configFiles, configDir):
    for var in configFiles:
        if var not in config:
            raise MissingConfigOnServer(f'key: {var}')

    for varName, fileLocations in configFiles.items():
        varValue = replace_occurence(config[varName], config)
        for fileLocation in fileLocations:
            try:
                replace_occurences(
                    varName,
                    varValue,
                    configDir+fileLocation
                    )
            except Exception:
                raise WriteConfigError()