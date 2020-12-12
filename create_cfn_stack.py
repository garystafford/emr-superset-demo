#!/usr/bin/env python3

# Purpose: Create EMR bootstrap script bucket and deploy the cfn stack
# Author:  Gary A. Stafford (December 2020)
# Reference: https://gist.github.com/svrist/73e2d6175104f7ab4d201280acba049c
# Usage Example: python3 ./create_cfn_stack.py \
#                    --ec2-key-name emr-demo-123456789012-us-east-1 \
#                    --ec2-subnet-id subnet-06aa61f790a932b32

import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

sts_client = boto3.client('sts')
cfn_client = boto3.client('cloudformation')
region = boto3.DEFAULT_SESSION.region_name
s3_client = boto3.client('s3', region_name=region)

logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO)


def main():
    args = parse_args()

    # create bootstrap bucket
    account_id = sts_client.get_caller_identity()['Account']
    bootstrap_bucket = f'superset-emr-demo-bootstrap-{account_id}-{region}'
    create_bucket(bootstrap_bucket)

    # upload bootstrap script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    upload_file(f'{dir_path}/bootstrap_emr/bootstrap_actions.sh', bootstrap_bucket, 'bootstrap_actions.sh')

    # set variables
    stack_name = 'emr-superset-demo'
    cfn_template_path = f'{dir_path}/cloudformation/superset-emr-demo.yml'
    cfn_params_path = f'{dir_path}/cloudformation/superset-emr-demo-params.json'
    ec2_key_name = args.ec2_key_name

    # append new parameters
    cfn_params = _parse_parameters(cfn_params_path)
    cfn_params.append({'ParameterKey': 'Ec2KeyName', 'ParameterValue': ec2_key_name})
    cfn_params.append({'ParameterKey': 'Ec2SubnetId', 'ParameterValue': args.ec2_subnet_id})
    cfn_params.append({'ParameterKey': 'BootstrapBucket', 'ParameterValue': bootstrap_bucket})
    logging.info(json.dumps(cfn_params, indent=4))

    # create the cfn stack
    create_stack(stack_name, cfn_template_path, cfn_params)


def create_bucket(bootstrap_bucket):
    """Create an S3 bucket in a specified region

    :param bootstrap_bucket: Bucket to create
    :return: True if bucket created, else False
    """

    try:
        s3_client.create_bucket(Bucket=bootstrap_bucket)
        logging.info(f'New bucket name: {bootstrap_bucket}')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_file(file_name, bootstrap_bucket, object_name):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bootstrap_bucket: Bucket to upload to
    :param object_name: S3 object name
    :return: True if file was uploaded, else False
    """

    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bootstrap_bucket, object_name)
        logging.info(f'File {file_name} uploaded to bucket {bootstrap_bucket} as object {object_name}')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def create_stack(stack_name, cfn_template, cfn_params):
    template_data = _parse_template(cfn_template)

    create_stack_params = {
        'StackName': stack_name,
        'TemplateBody': template_data,
        'Parameters': cfn_params,
        'TimeoutInMinutes': 60,
        'Capabilities': [
            'CAPABILITY_NAMED_IAM',
        ],
        'Tags': [
            {
                'Key': 'Project',
                'Value': 'Superset EMR Demo'
            },
        ]
    }

    try:
        response = cfn_client.create_stack(**create_stack_params)
        logging.info(f'Response: {response}')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def _parse_template(template):
    with open(template) as template_file_obj:
        template_data = template_file_obj.read()
    cfn_client.validate_template(TemplateBody=template_data)
    return template_data


def _parse_parameters(parameters):
    with open(parameters) as parameter_file_obj:
        parameter_data = json.load(parameter_file_obj)
    return parameter_data


def parse_args():
    """Parse argument values from command-line"""

    parser = argparse.ArgumentParser(description='Arguments required for script.')
    parser.add_argument('--ec2-key-name', required=True, help='Ec2KeyName: Name of EC2 Keypair')
    parser.add_argument('--ec2-subnet-id', required=True, help='Ec2SubnetId: Name of EC2 Keypair')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
