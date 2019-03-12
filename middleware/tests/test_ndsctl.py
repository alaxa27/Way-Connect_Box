from unittest import TestCase
from unittest.mock import call, patch
from nameko.testing.services import worker_factory

from ndsctl import NdsctlService


class TestNdsctlService(TestCase):
    def setUp(self):
        self.service = worker_factory(NdsctlService)

    # def test_set_active_clients(self):
    #     self.service.set_active_clients(self.activeClientsMock)
    #     self.assertEqual(self.storedClientsMock, ['1', '2', '3', '4'])

    # def test_delete_inactive_clients(self):

    #     self.service.delete_inactive_clients(
    #         self.activeClientsMock,
    #         self.storedClientsMock
    #     )
    #     self.assertEqual(self.storedClientsMock, ['1', '2'])

    # @patch('ndsctl.NdsctlService.retrieve_client_list')
    # @patch('ndsctl.NdsctlService.call_ndsctl')
    # def test_update_clients(self, ndsctlMock, retrieveMock):
    #     scanMock = self.service.redis.scan_iter

    #     retrieveMock.return_value = self.activeClientsMock
    #     scanMock.return_value = self.storedClientsMock

    #     self.service.update_clients()

    #     for k, v in self.activeClientsMock.items():
    #         self.assertTrue(k in self.storedClientsMock)

    #     for i in self.storedClientsMock:
    #         self.assertTrue(i in self.activeClientsMock)

    # def test_get_client_mac(self):
    #     def get(key):
    #         return str({'mac': 'baz'})

    #     getMock = self.service.redis.get
    #     getMock.side_effect = get

    #     expectedResult = 'baz'
    #     result = self.service.get_client_mac('4')

    #     self.assertEqual(result, expectedResult)

    def test_retrieve_preauth_from_active(self):
        activeClients = {
            'a': {
                'ip': 'a',
                'state': 'EJFEOIZAJ',
                'mac': 'TRAZ45'
            },
            'b': {
                'ip': 'b',
                'mac': 4567,
                'state': 'Authenticated'
            },
            'c': {
                'ip': 'c',
                'state': 'Preauthenticated'
            }
        }

        expectedResult = {
            'c': {
                'ip': 'c',
                'state': 'Preauthenticated'
            }
        }
        result = self.service.retrieve_preauth_from_active(activeClients)

        self.assertEqual(result, expectedResult)
    
    def test_delete_inactive_connects(self):
        deleted = []
        def redis_delete(item):
            deleted.append(item)

        redisDeleteMock = self.service.redis.delete
        redisDeleteMock.side_effect = redis_delete

        preauthClients = {
            'a': {
                'foo': 'a'
            },
            'b': {
                'foo': 'b'
            }
        }
        
        connects = [b'connect:b', b'connect:c']

        expectedResult = [b'connect:c']
        self.service.delete_inactive_connects(preauthClients, connects)

        self.assertEqual(deleted, expectedResult)

    @patch('ndsctl.NdsctlService.fetch_set_connect')
    def test_set_active_connects(self, fetchSetMock):
        setted = []
        def fetch_set(item):
            setted.append(item)

        fetchSetMock.side_effect = fetch_set

        preauthClients = {
            'b': {
                'bar': 'b'
            },
            'c': {
                'bar': 'c'
            }
        }

        connects = [b'connect:a', b'connect:b']

        expectedResult = ['c']
        self.service.set_active_connects(preauthClients, connects)

        self.assertEqual(setted, expectedResult)
    
    @patch('ndsctl.NdsctlService.fetch_set_connect')
    def test_get_connect_from_ip_not_fetched(self, fetchSetMock):
        redisGetMock = self.service.redis.get
        redisGetMock.return_value = None

        self.service.get_connect_from_ip('a')

        fetchSetMock.assert_called_once_with('a')

    @patch('ndsctl.NdsctlService.fetch_set_connect')
    def test_get_connect_from_ip_fetched(self, fetchSetMock):
        redisGetMock = self.service.redis.get
        redisGetMock.return_value = "{'foo': 'bar'}"

        expectedResult = {'foo': 'bar'}
        result = self.service.get_connect_from_ip('a')

        self.assertEqual(result, expectedResult)

    def test_update_clients(self):
        redisSetMock = self.service.redis.set
        redisDeleteMock = self.service.redis.delete

        storedClients = (c for c in [b'client:a', b'client:b'])
        activeClients = {
            'b': {
                'bar': 'b'
            },
            'c': {
                'bar': 'c'
            }
        }

        self.service.update_clients(activeClients, storedClients)
        
        # test that setMock has been called with b and c
        redisSetMock.assert_has_calls([
            call('client:b', str(activeClients['b'])),
            call('client:c', str(activeClients['c']))
            ])

        # test that deleteMock has been called with a
        redisDeleteMock.assert_has_calls([call(b'client:a')])

    @patch('ndsctl.NdsctlService.fetch_set_connect')
    def test_update_connects(self, fetchSetMock):
        redisDeleteMock = self.service.redis.delete

        activeClients = {
            'b': {
                'bar': 'b',
                'state': 'Preauthenticated'
            },
            'c': {
                'bar': 'c',
                'state': 'Preauthenticated'
            },
            'd': {
                'bar': 'k'
            },
            'f': {
                'bar': 'd',
                'state': 'Authenticated'
            },
            'e': {
                'bar': 'd',
                'state': 'foo'
            }
        }

        connects = [b'connect:a', b'connect:b']

        self.service.update_connects(activeClients, connects)

        # test that fetchSetMock called once with c
        fetchSetMock.assert_called_once_with('c')
        # test that deleteMock has calls a
        redisDeleteMock.assert_has_calls([call(b'connect:a')])

