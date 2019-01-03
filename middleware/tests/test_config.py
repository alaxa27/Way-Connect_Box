from unittest import TestCase
from unittest.mock import patch, call

import config


class TestConfig(TestCase):
    def test_write_config(self):
        pass
    
    @patch('subprocess.call')
    def test_reload_daemons(self, callMock):
        config.reload_daemons()
        callMock.assert_called_with('/bin/systemctl daemon-reload', shell=True)

    @patch('config.restart_services')
    def test_restart_updated_services(self, restartMock):
        """Only updated config's services should be restarted."""
        old = {
            'A': 0,
            'B': 3
        }
        new = {
            'B': 3,
            'A': 1
        }
        services = {
            'A': 'serviceA',
            'B': 'serviceB'
        }

        config.restart_updated_services(new, old, services)
        restartMock.assert_called_once_with('serviceA')

    @patch('config.restart_services')
    def test_restart_new_config_service(self, restartMock):
        """New config key's service should be restarted."""
        old = {
            'A': 0
        }
        new = {
            'A': 0,
            'B': 1
        }
        services = {
            'A': 'serviceA',
            'B': 'serviceB'
        }

        config.restart_updated_services(new, old, services)
        restartMock.assert_called_once_with('serviceB')

    @patch('config.restart_services')
    def test_restart_config_service_not_in_info(self, restartMock):
        """If a service needs to be restarted but is not present in the infos\
        nothing should happen.""" 
        old = {
            'A': 0
        }
        new = {
            'A': 1,
            'B': 3
        }
        services = {
        }

        try:
            config.restart_updated_services(new, old, services)
        except config.RestartUpdatedServicesError:
            self.fail('It should not raise RestartUpdateServicesError')

        restartMock.assert_not_called()

    def test_restart_remote_key_not_exist(self):
        """If a service is present in the configInfo but not on the remote, it\
        should raise a RestartUpdateServicesError"""
        old = {}
        
        new = {}

        services = {
            'A': 'serviceA'
        }

        with self.assertRaises(config.RestartUpdatedServicesError):
            config.restart_updated_services(new, old, services)

    @patch('subprocess.call')
    @patch('utils.reboot')
    def test_restart_services_monit_reboot(self, rebootMock, subCallMock):
        """If monit then reboot needs to be reload, monit reload and systemctl
        restart monit then reboot"""
        config.restart_services(['monit', 'reboot'])
        subCallMock.assert_has_calls([
            call(['monit', 'reload']),
            call(['systemctl', 'restart', 'monit'])
        ])
        self.assertEqual(rebootMock.call_count, 1)

    def test_get_config_files(self):
        """Should retrieve the right paths associated with the right key."""
        remoteConfig = {
            'A': 2,
            'FILES_A': 'a;b;c',
            'SERVICES_A': 'd;e;f',
            'FILES_B': 'r;t;y'
        }
        configFiles = config.get_list_from_config(remoteConfig, 'FILES')

        expectedResult = {
            'A': ['a', 'b', 'c'],
            'B': ['r', 't', 'y']
        }
        self.assertEqual(configFiles, expectedResult)

    def test_get_config_services(self):
        """Should retrieve the right services associated with the right key."""
        remoteConfig = {
            'A': 1,
            'FILES_A': 'a;b;c',
            'SERVICES_A': 'd;e;f',
            'FILES_B': 'r;t;y',
            'SERVICES_C': 'p;o;g'
        }
        configFiles = config.get_list_from_config(remoteConfig, 'SERVICES')

        expectedResult = {
            'A': ['d', 'e', 'f'],
            'C': ['p', 'o', 'g']
        }
        self.assertEqual(configFiles, expectedResult)
