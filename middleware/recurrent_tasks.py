#!/usr/bin/env python3.7
from dotenv import load_dotenv, main
import fileinput
import git
import os
from pathlib import Path
import requests
import subprocess
import sys

from utils import sign, post_box_status, get_crons, write_crons, save_crons
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
        '/etc/nodogsplash/htdocs/splash.html'
    ],
    'ESTABLISHMENT_NAME': [
        '/etc/hostapd/hostapd.conf'
    ]
}


class FetchConfigError(Exception):
    pass


class FetchEstablishmentError(Exception):
    pass


class UnableToWriteConfig(Exception):
    pass


class MissingConfigOnServer(Exception):
    pass


class MissingKeyInConfig(Exception):
    pass


class UpdateFetchingError(Exception):
    pass


class HeadAlreadyExists(Exception):
    pass


class BranchDoesNotExist(Exception):
    pass


class ApplyCommitError(Exception):
    pass


class ApplySameCommitException(Exception):
    pass


class PutVersionError(Exception):
    pass


class UnableToApplyCrontab(Exception):
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
        raise ApplyCommitError(f'Failed to apply commit : {commit}; {str(e)}')


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


def get_box_config():
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
            url=f'https://{remoteHost}/customers/establishment/',
            headers=headers
        )
    except Exception as e:
        raise FetchEstablishmentError(e)

    response['ESTABLISHMENT_NAME'] = establishmentInfo.json()['name']
    response['API_KEY'] = API_KEY
    response['API_SECRET'] = API_SECRET
    return response


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


def apply_crontab(config, cronFile):
    print('Retrieving crons from config...', end='')
    try:
        crons = get_crons(config)
    except KeyError:
        print('FAIL')
        raise UnableToApplyCrontab(str(e))
    print('OK')

    print('Writing crons to cronjob file...', end='')
    try:
        write_crons(crons, cronFile)
    except utils.CronWritingError:
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


def run_update(repoPath, config):  # noqa: C901
    repo = git.Repo(repoPath)

    print('Fetching repo...', end='')
    try:
        fetch_repo(repo)
    except UpdateFetchingError as e:
        post_box_status(True, update_running=False, update_message=str(e))
        sys.exit(1)
    print('OK')

    print('Retrieving branch ID from config...', end='')
    try:
        branch = get_config_key(config, 'GIT_BRANCH')
    except MissingKeyInConfig as e:
        post_box_status(True, update_running=False, update_message=str(e))
        sys.exit(1)
    print('OK')

    print('Checking if branch exists...', end='')
    try:
        check_branch_exist(repo, branch)
    except BranchDoesNotExist as e:
        post_box_status(True, update_running=False, update_message=str(e))
        sys.exit(1)
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
        print(f'Apply commit error: {e}')
        post_box_status(True, update_running=False, update_message=str(e))
        sys.exit(1)
    except ApplySameCommitException:
        print('PASS')
        print('Commit already applied.')
        return False

    print('Sending update confirmation to API...', end='')
    try:
        put_box_version(commit)
    except PutVersionError as e:
        post_box_status(True, update_running=False, update_message=str(e))
        sys.exit(1)
    print('OK')
    return True


if __name__ == '__main__':
    envPath = f'{homePath}/env'
    repoPath = f'{homePath}/Way-Connect_Box'
    configDir = f'{repoPath}/config'
    etcDir = '/etc'

    currentConfig = get_current_config(envPath)
    try:
        remoteConfig = get_box_config()
    except FetchConfigError as e:
        post_box_status(
            True,
            internet_connection_active=False,
            internet_connection_message=f'Error fetching config: {str(e)}'
        )
    except FetchEstablishmentError as e:
        post_box_status(
            True,
            internet_connection_active=False,
            internet_connection_message=f'Error fetching establishment:{str(e)}'
        )

    print('--------------Running update--------------')
    updateStatus = run_update(repoPath, remoteConfig)
    print('------------------------------------------')

    if remoteConfig != currentConfig or updateStatus:
        copy_default_config(configDir, etcDir)
        try:
            apply_config(remoteConfig, configFilesLocations)
        except MissingConfigOnServer:
            post_box_status(False)
            sys.exit(1)

        try:
            save_config(remoteConfig, envPath)
        except UnableToWriteConfig:
            sys.exit(1)

        reboot()
        
    cronFile = f'{homePath}/cronjobs'
    print('------------Applying crontabs------------')
    try:
        apply_crontab(remoteConfig, cronFile)
    except UnableToApplyCrontab as e:
        post_box_status(
            False,
            update_running=False,
            update_message=f'Error applying crontab: {str(e)}'
            )
        sys.exit(1)
    print('-----------------------------------------')

    post_box_status(True)
