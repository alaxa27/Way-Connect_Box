#!/usr/bin/env python3.7
from dotenv import load_dotenv, main
import fileinput
import git
import os
from pathlib import Path
import requests
import subprocess
import sys

from utils import sign, post_box_status, put_box_version, get_crons, write_crons, save_crons
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
    def __init__(self, message):
        super().__init__(f'ApplyCommitError: ${message}')


class ApplyCrontabError(Exception):
    pass


class ApplySameCommitException(Exception):
    pass


class BranchDoesNotExist(Exception):
    pass


class FetchConfigError(Exception):
    def __init__(self, message):
        super().__init__(f'FetchConfigError: ${message}')


class FetchEstablishmentError(Exception):
    pass


class HeadAlreadyExists(Exception):
    pass


class MissingConfigOnServer(Exception):
    pass


class MissingKeyInConfig(Exception):
    pass


class PutVersionError(Exception):
    pass


class RunningUpdateError(Exception):
    pass


class UpdateFetchingError(Exception):
    pass


class WriteConfigError(Exception):
    pass


def check_branch_exist(repo, branch):
    try:
        repo.create_head(branch, repo.remotes.origin.refs[branch])
    except AttributeError as e:
        raise BranchDoesNotExist(
            f'Failed to create the head for {branch}; {str(e)}'
        )
    except Exception as e:
        raise HeadAlreadyExists(f'Head already exists; {str(e)}')
    return True


def fetch_repo(repo):
    try:
        repo.remotes.origin.fetch()
    except Exception as e:
        raise UpdateFetchingError(f'Error while fetching github repo; {e}')


def get_last_commit(repo, branch):
    return str(repo.commit(f'origin/{branch}'))


def apply_commit(repo, commit):
    isSameCommit = str(repo.commit()) == commit
    if (isSameCommit):
        raise ApplySameCommitException(
            f'Commit {commit} is already applied.'
        )
    print("commit", commit)
    try:
        repo.git.reset(commit, '--hard')
    except Exception as e:
        raise ApplyCommitError(f'<{commit}> {str(e)}')


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


def run_update(repoPath, config):  # noqa: C901
    repo = git.Repo(repoPath)

    print('Fetching repo...', end='')
    try:
        fetch_repo(repo)
    except UpdateFetchingError as e:
        raise RunningUpdateError(e)
    print('OK')

    print('Retrieving branch ID from config...', end='')
    try:
        branch = get_config_key(config, 'GIT_BRANCH')
    except MissingKeyInConfig as e:
        raise RunningUpdateError(e)
    print('OK')

    print('Checking if branch exists...', end='')
    try:
        check_branch_exist(repo, branch)
    except BranchDoesNotExist as e:
        raise RunningUpdateError(e)
    except HeadAlreadyExists:
        pass
    print('OK')

    print('Retrieving commit ID from config...', end='')
    try:
        commit = get_config_key(config, 'GIT_COMMIT')
        print('OK')
    except MissingKeyInConfig:
        print('FAIL')
        print('Retrieving commit ID from last branch commit...', end='')
        commit = get_last_commit(repo, branch)
        print('OK')

    print(f'Applying commit {commit}...', end='')
    try:
        apply_commit(repo, commit)
    except ApplyCommitError as e:
        print('FAIL')
        raise RunningUpdateError(e)
    except ApplySameCommitException:
        print('PASS')
        print('Commit already applied.')
        return False

    print('Sending update confirmation to API...', end='')
    try:
        put_box_version(commit)
    except PutVersionError as e:
        raise RunningUpdateError(e)
    print('OK')
    return True


def apply_crontab(config, cronFile):
    print('Retrieving crons from config...', end='')
    try:
        crons = get_crons(config)
    except KeyError as e:
        print('FAIL')
        raise UnableToApplyCrontab(str(e))
    print('OK')

    print('Writing crons to cronjob file...', end='')
    try:
        write_crons(crons, cronFile)
    except utils.CronWritingError as e:
        print('FAIL')
        raise UnableToApplyCrontab(str(e))
    print('OK')
    
    print('Saving new crons...', end='')
    try:
        save_crons(cronFile)
    except utils.CrontabExecutionFailed as e:
        print('FAIL')
        raise UnableToApplyCrontab(str(e))
    print('OK')


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
