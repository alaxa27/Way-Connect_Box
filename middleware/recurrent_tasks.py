#!/usr/bin/env python3.7
from config import apply_config, fetch_config, save_config
from config import ApplyConfigError, FetchConfigError, SaveConfigError
from crontab import apply_crontab
from crontab import ApplyCrontabError
from update import run_update
from update import RunUpdateError
from utils import post_error_status, post_service_status, reboot


homePath = '/home/pi'

configFilesLocations = {
    'INTERFACE_IN': [
        '/iptables.ipv4.nat',
        '/network/interfaces'
    ],
    'INTERFACE_OUT': [
        '/nodogsplash/nodogsplash.conf',
        '/dnsmasq.conf',
        '/iptables.ipv4.nat',
        '/network/interfaces'
    ],
    'PORTAL_HOST': [
        '/nginx/sites-enabled/storage_reverse_proxy.conf',
        '/nginx/sites-enabled/portal_reverse_proxy.conf'
    ],
    'ESTABLISHMENT_NAME': [
        '/hostapd/hostapd.conf'
    ],
    'NDS_CLIENT_FORCE_TIMEOUT': [
        '/nodogsplash/nodogsplash.conf'
    ],
    'NGROK_SUBDOMAIN': [
        '/ngrok.yml'
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
    except FetchConfigError:
        post_error_status('config')
    print('------------------------------------------')
    print('----------------Run Update----------------')
    try:
        updateStatus = run_update(repoPath, remoteConfig)
    except RunUpdateError:
        post_error_status('update')
    print('------------------------------------------')

    if currentConfig != remoteConfig or updateStatus:
        print('---------------Apply Config---------------')
        try:
            apply_config(remoteConfig, configFilesLocations, configDir, etcDir)
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
        reboot()

    post_service_status()
