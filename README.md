# Installing Apache Superset on Amazon EMR: Creating an Alternate User Interface for Amazon Athena

## Overview

Project files for the post, [Installing Apache Superset on Amazon EMR](https://garystafford.medium.com/). Please see post for complete instructions on using the project's files.


## Notes

- Athena database connection
- EMR_EC2_DefaultRole role need athena access (e.g., managed policy: AmazonAthenaFullAccess)
- `awsathena+rest://athena.us-east-1.amazonaws.com:443/AwsDataCatalog?s3_staging_dir=s3://aws-athena-query-results-123456789012-us-east-1`

### Method #1
Run as a bootstraop script.

```shell script
export EC2_KEY_PAIR="<your_key_pair_name>"
export SUBNET_ID="<your_subnet_name>"

python3 ./create_cfn_stack.py \
    --ec2-key-name ${EC2_KEY_PAIR} \
    --ec2-subnet-id ${SUBNET_ID}
```
### Method #2

Copy script to Master node and then execute.

```shell script
export MASTER_NODE_DNS=ec2-18-234-23-209.compute-1.amazonaws.com
export EC2_KEY_PATH=~/.ssh/emr-demo-123456789012-us-east-1.pem

scp -i ${EC2_KEY} \
    bootstrap_actions.sh hadoop@${MASTER_NODE_DNS}:~

ssh -i ~/.ssh/${EC2_KEY_PATH} \
    hadoop@${MASTER_NODE_DNS} "sh ./bootstrap_actions_ssh.sh"
```

Sample Athena query from Superset

```sql
SELECT upper(symbol)        AS symbol,
       round(AVG(close), 2) AS avg_close,
       round(MIN(low), 2)   AS min_low,
       round(MAX(high), 2)  AS max_high
FROM emr_demo.processed_stocks
GROUP BY symbol
ORDER BY avg_close DESC
LIMIT 10;
```

# References

- https://superset.apache.org/docs/installation/installing-superset-from-scratch
- https://gitmemory.com/issue/apache/incubator-superset/8169/528679887
- https://stackoverflow.com/questions/59195394/apache-superset-config-py-on