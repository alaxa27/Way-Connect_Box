#!/usr/bin/env python3.7
import argparse
from config import (
    apply_config,
    fetch_config,
    save_config
    )
from config import (
    ApplyConfigError,
    FetchConfigError,
    SaveConfigError
    )
from crontab import apply_crontab
from crontab import ApplyCrontabError
from status import post_service_status, post_error_status
from status import PostServiceStatusError
from update import run_update
from update import RunUpdateError
from utils import reboot

homePath = '/home/pi'

parser = argparse.ArgumentParser(description='WayBox vital tasks programm.')
parser.add_argument(
    '--update-config',
    action='store_true',
    help='downloads and updates config from back-end'
)
parser.add_argument(
    '--post-status',
    action='store_true',
    help='post box status to back-end'
)
parser.add_argument(
    '--reboot',
    action='store_true',
    help='reboot the WayBox'
)
args = vars(parser.parse_args())

if __name__ == '__main__':
    envFile = f'{homePath}/env'
    repoPath = f'{homePath}/Way-Connect_Box'
    cronFile = f'{homePath}/cronjobs'
    configDir = f'{repoPath}/config'
    etcDir = '/etc'

    print('---------------Fetch Config---------------')
    try:
        currentConfig, remoteConfig = fetch_config(envFile)
    except FetchConfigError:
        post_error_status('config')
    print('------------------------------------------')

    print('----------------Run Update----------------')
    try:
        run_update(repoPath, remoteConfig)
    except RunUpdateError:
        post_error_status('update')
    print('------------------------------------------')

    updateConfig = args['update_config']
    if currentConfig != remoteConfig or updateConfig:
        print('---------------Apply Config---------------')
        try:
            apply_config(remoteConfig, currentConfig, configDir, etcDir)
        except ApplyConfigError:
            post_error_status('config')
        print('------------------------------------------')

        print('--------------Apply Crontab---------------')
        try:
            apply_crontab(remoteConfig, cronFile)
        except ApplyCrontabError:
            post_error_status('crontab')
        print('------------------------------------------')

        print('----------------Save Config---------------')
        try:
            save_config(remoteConfig, envFile)
        except SaveConfigError:
            post_error_status('config')
        print('------------------------------------------')

    postStatus = args['post_status']
    if postStatus:
        print('------------Post Service Status-----------')
        try:
            post_service_status()
        except PostServiceStatusError:
            post_error_status('status')
        print('------------------------------------------')
    
    rebootArg = args['reboot']
    if rebootArg:
        reboot()
