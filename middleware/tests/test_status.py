import traceback
from unittest import TestCase
from unittest.mock import MagicMock, patch

import status


class TestStatus(TestCase):
    @patch('traceback.print_exc')
    @patch('sys.exit')
    @patch('status.post_box_status')
    def test_post_error_status(self, postMock, _, printExcMock):
        """should return the correct traceback and type"""
        type = 'testType'
        try:
            try:
                raise Exception('A')
            except Exception:
                raise Exception('B')
        except Exception:
            tb = traceback.format_exc()
            status.post_error_status(type)

        expectedMessage = {
            'error_type': type,
            'error_traceback': str(tb)
        }

        postMock.assert_called_with(
            internet_connection_active=False,
            internet_connection_message=expectedMessage
            )
        printExcMock.assert_called()

    @patch('subprocess.check_output')
    def test_retrieve_service_status(self, checkOutputMock):
        checkOutputMock.return_value = 'A=foo\nB=bar\n'
        expectedResult = {'A': 'foo', 'B': 'bar'}
        result = status.retrieve_service_status('test')

        self.assertEqual(result, expectedResult)

    @patch('status.post_box_status')
    def test_post_service_status(
        state,
        postBoxStatusMock,
    ):
        def retrieve_service_status_side_effect(serviceName):
            if serviceName == 'ngrok':
                return 'failed'
            return 'tst'

        def service_state_side_effect(statusDict):
            if statusDict == 'failed':
                return False
            return True

        serviceStateMock = MagicMock(
            name='status.service_state',
            side_effect=service_state_side_effect
            )
        retrieveServiceStatusMock = MagicMock(
            name='status.retrieve_service_status',
            side_effect=retrieve_service_status_side_effect
            )
        with patch('status.retrieve_service_status', retrieveServiceStatusMock),\
                patch('status.service_state', serviceStateMock):
            status.post_service_status()

        postBoxStatusMock.assert_called_with(
            dhcpd_running=True,
            dhcpd_message='{}',
            dnsmasq_running=True,
            dnsmasq_message='{}',
            hostapd_running=True,
            hostapd_message='{}',
            nodogsplash_running=True,
            nodogsplash_message='{}',
            update_running=False,
            update_message='failed',
            )

    def test_service_state(self):
        result = status.service_state({
            'ActiveState': 'active'
        }) 
        expectedResult = True

        self.assertEqual(result, expectedResult)

        result = status.service_state({
            'ActiveState': 'foo'
        }) 
        expectedResult = False

        self.assertEqual(result, expectedResult)
