#!/usr/bin/env python3.7
import sys

from config import apply_config, fetch_config, save_config
from config import ApplyConfigError, FetchConfigError, SaveConfigError
from crontab import apply_crontab
from crontab import ApplyCrontabError
from update import run_update
from update import RunUpdateError
from utils import post_box_status, reboot


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
    except RunUpdateError as e:
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
            post_box_status(crontab_running=False, crontab_message=str(e))
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
