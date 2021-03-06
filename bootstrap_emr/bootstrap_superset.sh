#!/bin/bash

# Purpose: Installs Apache Superset on EMR
# Author:  Gary A. Stafford (December 2020)
# Usage: sh ./bootstrap_superset.sh 8280
# Reference: https://superset.apache.org/docs/installation/installing-superset-from-scratch

# port for superset (default: 8280)
SUPERSET_PORT="${1:-8280}"

# install required packages
sudo yum -y install gcc gcc-c++ libffi-devel python-devel python-pip python-wheel \
  openssl-devel cyrus-sasl-devel openldap-devel python3-devel.x86_64

# optionally, update master node packages
sudo yum -y update

# set up a python virtual environment
python3 -m pip install --user --upgrade setuptools virtualenv
python3 -m venv venv
. venv/bin/activate

python3 -m pip install --upgrade apache-superset \
  PyAthenaJDBC PyAthena sqlalchemy-redshift pyhive mysqlclient psycopg2-binary

command -v superset

superset db upgrade

FLASK_APP=superset
export "FLASK_APP=${FLASK_APP}"
echo "export FLASK_APP=superset" >>~/.bashrc

touch superset_config.py
echo "ENABLE_TIME_ROTATE = True" >>superset_config.py
echo "export SUPERSET_CONFIG_PATH=superset_config.py" >>~/.bashrc

ADMIN_USERNAME="SupersetAdmin"
ADMIN_PASSWORD="Admin1234"

# create superset admin
superset fab create-admin \
  --username "${ADMIN_USERNAME}" \
  --firstname Superset \
  --lastname Admin \
  --email superset_admin@example.com \
  --password "${ADMIN_PASSWORD}"

superset init

# create two sample superset users
superset fab create-user \
  --role Alpha \
  --username SupersetUserAlpha \
  --firstname Superset \
  --lastname UserAlpha \
  --email superset_user_alpha@example.com \
  --password UserAlpha1234

superset fab create-user \
  --role Gamma \
  --username SupersetUserGamma \
  --firstname Superset \
  --lastname UserGamma \
  --email superset_user_gamma@example.com \
  --password UserGamma1234

# get ec2 instance id
INSTANCE_ID="$(curl --silent http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .instanceId)"

# use ec2 instance id to get public dns of master node
PUBLIC_MASTER_DNS="$(aws ec2 describe-instances --instance-id ${INSTANCE_ID} |
  jq -r '.Reservations[0].Instances[0].PublicDnsName')"

# start superset in background
nohup superset run \
  --host "${PUBLIC_MASTER_DNS}" \
  --port "${SUPERSET_PORT}" \
  --with-threads --reload --debugger \
  >superset_output.log 2>&1 </dev/null &

# output superset connection info
printf %s """
**********************************************************************
  Superset URL: http://${PUBLIC_MASTER_DNS}:${SUPERSET_PORT}
  Admin Username: ${ADMIN_USERNAME}
  Admin Password: ${ADMIN_PASSWORD}
**********************************************************************
"""