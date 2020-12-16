#!/usr/bin/env python3

# Purpose: Install Apache Superset on EMR Master Node
# Author:  Gary A. Stafford (December 2020)
# Usage Example: python3 ./create_cfn_stack.py \
#                    --master-node-dns ec2-111-22-333-44.compute-1.amazonaws.com \
#                    --ec2-key-path ~/.ssh/emr-demo-123456789012-us-east-1.pem \
#                    --superset-port 8280

import argparse
import logging
import os

from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO)


def main():
    args = parse_args()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file = f'{dir_path}/bootstrap_emr/bootstrap_superset.sh'

    username = 'hadoop'

    # upload bootstrap script
    install_superset(file, args.master_node_dns, username, args.ec2_key_path, args.superset_port)


def install_superset(file, master_node_dns, username, ec2_key_path, superset_port):
    """SCP script to EMR Master Node and run"""

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    ssh.connect(hostname=master_node_dns, username=username, key_filename=ec2_key_path)

    with SCPClient(ssh.get_transport()) as scp:
        scp.put(file)

    stdin_, stdout_, stderr_ = ssh.exec_command(
        command=f'sh ./bootstrap_superset.sh ${superset_port}', get_pty=True)
    stdout_.channel.recv_exit_status()
    lines = stdout_.readlines()
    for line in lines:
        logging.info(line)

    ssh.close()


def parse_args():
    """Parse argument values from command-line"""

    parser = argparse.ArgumentParser(description='Arguments required for script.')
    parser.add_argument('-d', '--master-node-dns', required=True, help='Master Node DNS')
    parser.add_argument('-e', '--ec2-key-path', required=True, help='EC2 Key Path')
    parser.add_argument('-s', '--superset-port', default=8280, help='Apache Superset Port')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
