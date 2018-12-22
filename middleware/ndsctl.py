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

    redis = Redis('development')

    @rpc
    def auth_client(self, ip):
        try:
            self.call_ndsctl(['auth', 'ip'])
        except NdsctlExecutionFailed:
            raise AuthenticationFailed()

    def call_ndsctl(params):
        args = ['/usr/bin/ndsctl']
        args += params
        try:
            output = subprocess.check_output(args)
        except OSError:
            raise NdsctlExecutionFailed()
        except subprocess.SubprocessError:
            raise NdsctlExecutionFailed()

        return json.loads(output)

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
        client = eval(client)
        return client['mac'] 

    def retrieve_client_list(output):
        clients = output['clients']
        clientsObject = {}

        for clientMac, clientInfo in clients.items():
            client = {}
            clientIP = clientInfo['ip']

            client['mac'] = clientMac
            client['ip'] = clientIP
            client['token'] = clientInfo['token']
            clientsObject[f'client:{clientIP}'] = client

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