#!/bin/bash

# Purpose: EMR bootstrap script that installs Superset
# Author:  Gary A. Stafford (December 2020)
# Reference: https://superset.apache.org/docs/installation/installing-superset-from-scratch

# set aws region for boto3
aws configure set region \
  "$(curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)"

# update and install required packages
yes | sudo yum update
yes | sudo yum install jq gcc gcc-c++ libffi-devel python-devel python-pip python-wheel \
    openssl-devel cyrus-sasl-devel openldap-devel boto3 ec2-metadata awswrangler
yes | sudo yum install python3-devel.x86_64 # will get errors installing superset without this extra step

# install required Python package
python3 -m pip install --user --upgrade setuptools pip virtualenv

python3 -m venv venv
. venv/bin/activate

# install and upgrade superset
python3 -m pip install apache-superset
superset db upgrade

# install Amazon Athena, RedShift, Spark SQL/Presto database driver
# https://superset.apache.org/docs/databases/installing-database-drivers
python3 -m pip install PyAthenaJDBC>1.0.9 PyAthena>1.2.0 sqlalchemy-redshift pyhive

echo "export FLASK_APP=superset" >> ~/.bashrc

export PYTHON_DIR="$(ls ~/venv/lib/ | head 1)" # should only be one dir in there
echo "export SUPERSET_HOME=~/venv/lib/${PYTHON_DIR}/site-packages/superset/" >> ~/.bashrc

# enabling logging
# e.g. location: /home/hadoop/venv/lib64/python3.7/site-packages/superset/superset.log
touch superset_config.py
echo "ENABLE_TIME_ROTATE = True" >> "\~/venv/lib/${PYTHON_DIR}/site-packages/superset/superset_config.py"
echo "export SUPERSET_CONFIG_PATH=~/superset_config.py" >> ~/.bashrc

ADMIN_USERNAME="SupersetAdmin"
ADMIN_PASSWORD="Admin1234!"

# create superset admin
superset fab create-admin \
    --username ${ADMIN_USERNAME} \
    --firstname Superset \
    --lastname Admin \
    --email superset_admin@example.com \
    --password ${ADMIN_PASSWORD}

# load example datasets
superset load_examples
superset init

# create two sample superset users
superset fab create-user \
    --role Alpha \
    --username SupersetUserAlpha \
    --firstname Superset \
    --lastname UserAlpha \
    --email superset_user_alpha@example.com \
    --password UserAlpha1234!

superset fab create-user \
    --role Gamma \
    --username SupersetUserGamma \
    --firstname Superset \
    --lastname UserGamma \
    --email superset_user_gamma@example.com \
    --password UserGamma1234!

# get instance id
export INSTANCE_ID="$(curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .instanceId)"

# use instance id to get public dns of master node
export PUBLIC_MASTER_DNS="$(aws ec2 describe-instances --instance-id ${INSTANCE_ID} | jq -r '.Reservations[0].Instances[0].PublicDnsName')"

# chose an open port for superset
export SUPERSET_WEBSERVER_PORT=8280

# start superset in background
nohup superset run \
    --host ${PUBLIC_MASTER_DNS} \
    --port ${SUPERSET_WEBSERVER_PORT} \
    --with-threads --reload --debugger \
    >superset_output.log 2>&1 </dev/null &

echo "Apache Superset UI URL: http://${PUBLIC_MASTER_DNS}:${SUPERSET_WEBSERVER_PORT}"
echo "Superset Admin Username: ${ADMIN_USERNAME}, Password: ${ADMIN_PASSWORD}"