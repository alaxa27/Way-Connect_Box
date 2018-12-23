import json
import subprocess
from nameko.rpc import rpc
from nameko.timer import timer
from nameko_redis import Redis


class AuthenticationFailed(Exception):
    pass


class NdsctlExecutionFailed(Exception):
    pass


class KeyMissingInNdsctlOutput(Exception):
    pass


class UpdateClientsError(Exception):
    pass


class NdsctlService:
    name = 'ndsctl_service'

    redis = Redis('ndsctl')

    @rpc
    def auth_client(self, ip):
        try:
            response = self.call_ndsctl(['auth', ip])
        except NdsctlExecutionFailed:
            raise AuthenticationFailed()
        if 'Fail' in str(response):
            raise AuthenticationFailed('Fail in response.')
        return True

    def call_ndsctl(self, params):
        args = ['/usr/bin/ndsctl']
        args += params
        try:
            output = subprocess.check_output(args)
        except OSError:
            raise NdsctlExecutionFailed(args)
        except subprocess.SubprocessError:
            raise NdsctlExecutionFailed(args)
        except subprocess.CalledProcessError:
            raise NdsctlExecutionFailed(args)

        try:
            jsonOutput = json.loads(output)
        except json.decoder.JSONDecodeError:
            return None
        return jsonOutput

    def delete_inactive_clients(self, activeClients, storedClients):
        for storedClient in storedClients:
            try:
                activeClients[storedClient]
            except KeyError:
                self.redis.delete(storedClient)

    def get_clients(self):
        clients = []
        for client in self.redis.scan_iter(match='client:*'):
            client = self.redis.get(client)
            clients.append(client)
        return clients

    @rpc
    def get_client_mac(self, ip):
        client = self.redis.get(f'client:{ip}')
        if client:
            client = eval(client)
            return client['mac'] 
        return '22:22:22:22:22:22'

    def retrieve_client_list(self, output):
        clients = output['clients']
        clientsObject = {}

        for clientMac, clientInfo in clients.items():
            client = {}
            clientIP = clientInfo['ip']

            client['mac'] = clientMac
            client['ip'] = clientIP
            client['token'] = clientInfo['token']
            clientsObject[clientIP] = client

        return clientsObject

    def set_active_clients(self, clients):
        for clientIP, client in clients.items():
            self.redis.set(f'client:{clientIP}', str(client))

    @timer(interval=1)
    def update_clients(self):
        try:
            output = self.call_ndsctl(['json'])
        except NdsctlExecutionFailed:
            raise UpdateClientsError()
        activeClients = self.retrieve_client_list(output)
        storedClients = self.redis.scan_iter(match='client:*')

        self.delete_inactive_clients(activeClients, storedClients)
        self.set_active_clients(activeClients)
