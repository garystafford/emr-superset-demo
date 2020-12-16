#!/usr/bin/env python3

# Delete Super EMR Demo buckets
# Author: Gary A. Stafford (November 2020)

import logging

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO)

s3_client = boto3.resource('s3')
sts_client = boto3.client('sts')


def main():
    region = boto3.DEFAULT_SESSION.region_name
    account_id = sts_client.get_caller_identity()['Account']

    bootstrap_bucket = f'superset-emr-demo-bootstrap-{account_id}-{region}'
    logs_bucket = f'superset-emr-demo-logs-{account_id}-{region}'

    delete_buckets([bootstrap_bucket, logs_bucket])


def delete_buckets(buckets):
    """ Delete all Amazon S3 buckets created for this project """

    for bucket in buckets:
        try:
            bucket_to_delete = s3_client.Bucket(bucket)
            bucket_to_delete.object_versions.delete()
            bucket_to_delete.delete()
            logging.info(f"Bucket deleted: {bucket}")
        except ClientError as e:
            logging.error(e)


if __name__ == '__main__':
    main()
