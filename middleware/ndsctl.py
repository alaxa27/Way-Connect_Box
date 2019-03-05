import json
import subprocess
from nameko.rpc import rpc
from nameko.timer import timer
from nameko_redis import Redis


class AuthenticationFailed(Exception):
    pass


class DeleteInactiveClientsError(Exception):
    pass


class DeleteInactiveConnectsError(Exception):
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
        if 'authenticated' in str(response):
            return True
        raise AuthenticationFailed('Fail in response.')

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
            return output
        return jsonOutput

    def delete_inactive_clients(self, activeClients, storedClients):
        for storedClient in storedClients:
            try:
                storedClientip = storedClient.decode('utf-8').split(':')[1]
            except IndexError:
                raise DeleteInactiveClientsError(storedClient)
            try:
                activeClients[storedClientip]
            except KeyError:
                self.redis.delete(storedClient)

    def delete_inactive_connects(self, clients, connects):
        for connect in connects:
            try:
                connectip = connect.decode('utf-8').split(':')[1]
            except IndexError:
                raise DeleteInactiveConnectsError(connect)
            try:
                clients[connectip]
            except KeyError:
                self.redis.delete(connect)

    def fetch_connect(self, client):
        return {'foo': 'bar'}

    def fetch_set_connect(self, ip):
        client = self.redis.get(f'client:{ip}')
        connectResult = self.fetch_connect(client)
        self.redis.set(f'connect:{ip}', str(connectResult))

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
    
    @rpc
    def get_connect_from_ip(self, ip):
        connect = f'connect:{ip}'
        connectData = self.redis.get(connect)
        if connectData:
            return eval(connectData)

        self.fetch_set_connect(ip)

    def retrieve_preauth_from_active(self, clients):
        preauthClients = {}
        for clientIP, client in clients.items():
            if client['state'] == 'Preauthenticated':
                preauthClients[clientIP] = client

        return preauthClients

    def retrieve_client_list(self, output):
        clients = output['clients']
        clientsObject = {}

        for _, clientInfo in clients.items():
            client = clientInfo
            clientIP = clientInfo['ip']

            clientsObject[clientIP] = client

        return clientsObject

    def set_active_clients(self, clients):
        for clientIP, client in clients.items():
            self.redis.set(f'client:{clientIP}', str(client))

    def set_active_connects(self, clients, connects):
        for clientIP, client in clients.items():
            connect = f'connect:{clientIP}'.encode('utf-8')
            if connect not in connects:
                self.fetch_set_connect(clientIP)

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
        
        connects = self.redis.scan_iter(match='connects:*')

        preauthClients = self.retrieve_preauth_from_active(activeClients)
        self.delete_inactive_connects(preauthClients, connects)
        self.set_active_connects(preauthClients, connects)
