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

    @patch('config.reload_services')
    def test_reload_updated_services(self, reloadMock):
        """Only updated config's services should be reloaded."""
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

        config.reload_updated_services(new, old, services)
        reloadMock.assert_called_once_with('serviceA')

    @patch('config.reload_services')
    def test_reload_new_config_service(self, reloadMock):
        """New config key's service should be reloaded."""
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

        config.reload_updated_services(new, old, services)
        reloadMock.assert_called_once_with('serviceB')

    def test_reload_config_service_not_in_info(self):
        """If a service needs to be reload but is not present in the infos
        it should raise the appropriate error."""
        old = {
            'A': 0
        }
        new = {
            'A': 1
        }
        services = {
        }
        
        with self.assertRaises(config.MissingKeyInConfigInfo):
            config.reload_updated_services(new, old, services)

    @patch('subprocess.call')
    @patch('utils.reboot')
    def test_reload_services_monit_reboot(self, rebootMock, subCallMock):
        """If monit then reboot needs to be reload, monit reload and systemctl
        restart monit then reboot"""
        config.reload_services(['monit', 'reboot'])
        subCallMock.assert_has_calls([
            call(['monit', 'reload']),
            call(['systemctl', 'restart', 'monit'])
        ])
        self.assertEqual(rebootMock.call_count, 1)
