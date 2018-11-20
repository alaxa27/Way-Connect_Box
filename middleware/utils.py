import hmac, hashlib, json
import subprocess


class NdsctlExecutionFailed(Exception):
    pass


class KeyMissingInNdsctlOutput(Exception):
    pass


def call_ndsctl():
    output = subprocess.check_output(['sudo', '/usr/bin/ndsctl', 'json'])
        
    return json.loads(output)


def retrieve_client_list(output):
    clients = output['clients']
    clientList =  []
    for clientMac, clientInfo in clients.items():
        client = {}
        client['mac'] = clientMac
        client['ip'] = clientInfo['ip']
        client['token'] = clientInfo['token']
        clientList.append(client)
        
    return clientList


def get_client_from_ip(ip):
    try: 
        ndsctlOutput = call_ndsctl()
    except OSError as e:
        raise NdsctlExecutionFailed(str(e))        
    except subprocess.SubprocessError as e:
        raise NdsctlExecutionFailed(str(e))

    try:
        clientList = retrieve_client_list(ndsctlOutput)
    except KeyError as e:
        raise KeyMissingInNdsctlOutput(str(e))
        
    for client in clientList:
        if client['ip'] == ip:
            return client
    result = {}
    result['ip'] = ip
    result['mac'] = '22:22:22:22:22:22'
    result['token'] = 'token'
    return result
    

def sign(public_key, secret_key, data):
    h = hmac.new(
        secret_key.encode('utf-8'), public_key.encode('utf-8'),
        digestmod=hashlib.sha1
    )
    h.update(json.dumps(data, sort_keys=True).encode('utf-8'))
    return str(h.hexdigest())
