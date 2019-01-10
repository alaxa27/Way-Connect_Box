#!/usr/bin/env python3
import argparse
import io
import json
import requests
import subprocess


parser = argparse.ArgumentParser(description='Connects to Way-Box through ssh.')
parser.add_argument(
        '-s',
        '--server',
        type=str,
        default='tunnel.way-connect.com',
        help='ngrokd domain name'
        )

parser.add_argument(
        '-u',
        '--user',
        type=str,
        help='the user on the remote',
        default='pi'
        )

parser.add_argument(
        '-k',
        '--key',
        type=str,
        help='the API key of the Way-Box',
        required=True
        )

parser.add_argument(
        '-c',
        '--connect',
        action='store_true',
        help='connects automatically'
        )

parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='explain what is being done'
        )

parser.add_argument(
        '--run-command',
        type=str,
        help='runs command remotely and print output to STDOUT'
        )

args = vars(parser.parse_args())


def get_port_from_url(url):
    return url.split(':')[-1]


def ssh_connect(url, user=None, port=22):
    if user:
        url = f'{user}@{url}'

    command = ['ssh', url, '-p', port] 
    command = ['/bin/sh', '-c', '"ssh {url} -p {port}"']

    subprocess.run(
        command,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False
        )


def ssh_run_command(url, command, user=None, port=22):
    if user:
        url = f'{user}@{url}'
    command = ['ssh', '-p', port, url, command]

    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"): 
        print(line)


if __name__ == '__main__':
    key = args['key']
    serverUrl = args['server']

    resp = requests.get(f'http://{key}.{serverUrl}:8000/api/tunnels')

    data = resp.json() # json.loads(resp.json)
    tunnels = data['Tunnels']
    if args['verbose']:
        print(json.dumps(tunnels, indent=4, sort_keys=True))
    for tunnel in tunnels:
        port = get_port_from_url(tunnel['LocalAddr'])
        if port == str(22):
            sshPort = get_port_from_url(tunnel['PublicUrl'])
            url = f'{key}.{serverUrl}'

            print(f'ssh {args["user"]}@{url} -p {sshPort}')
            if args['verbose']:
                print(f'Port: {sshPort}')
                print(f'URL: {url}')
            if args['run_command']:
                ssh_run_command(
                        url,
                        args['run_command'],
                        user=args['user'],
                        port=sshPort
                        )
            if args['connect']:
                ssh_connect(url, user=args['user'], port=sshPort)

