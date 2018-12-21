from unittest import TestCase
from unittest.mock import patch

import config


class TestConfig(TestCase):
    def test_write_config(self):
        pass
    
    @patch('subprocess.call')
    def test_reload_daemons(self, callMock):
        config.reload_daemons()
        callMock.assert_called_with('/bin/systemctl daemon-reload', shell=True)
