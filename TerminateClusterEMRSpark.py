#!/usr/bin/python3.6
#####################################################################################################################################
# NeoWay Interview
# Script to Terminate an EMR Cluster
# Cluster Options in configfile
# Dependencies: python3.6, boto3,configparser
# Notebooks will be stored in S3 bucket: https://s3.console.aws.amazon.com/s3/buckets/jupyterjose123/?region=us-east-2&tab=overview #
#####################################################################################################################################

import configparser
import boto3
from botocore.exceptions import ClientError
import sys
import os
import subprocess
import logging
import time
from datetime import datetime


#Get current pwd
#Get current pwd
abspath = os.path.abspath(__file__)
dirpath=os.path.dirname(abspath)



configfile=dirpath + '/clusterconfig.cnf'
clusteridfile=dirpath + '/clusterid'

DataLog = datetime.now().strftime("%Y%m%d")
Log=dirpath + '/TerminateClusterEMRSpark.log.' + DataLog
logging.basicConfig(filename=Log,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)



DataStart = datetime.now().strftime("%Y%m%d%H%M%S")
logging.info("------------------------------------------------------------------------")
logging.info("Start %s" % DataStart)
logging.info("Script para criar cluster spark")
logging.info("-----------------------------------------------------------------------------")





#Parse config file
logging.info("Parsing config file %s " % configfile)
config = configparser.ConfigParser()
config.read(configfile)
key_id=config['AWSCREDENTIALS']['aws_access_key_id']
access_key=config['AWSCREDENTIALS']['aws_secret_access_key']
region=config['AWSCREDENTIALS']['region_name']

logging.info("Terminating Cluster EMR")
client = boto3.client('emr',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key)

logging.info("Reading ClusterId from file %s" % clusteridfile)
with open(clusteridfile,'r') as fh:
    for line in fh:
        line=line.replace("\n","") 
        clusterid=line

client.terminate_job_flows(JobFlowIds=[clusterid])

logging.info("Waiting ...")
while True:
    client = boto3.client('emr',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key)
    response=client.describe_cluster(ClusterId=clusterid)
    status=response['Cluster']['Status']['State']
    if status=='TERMINATED':
        logging.info("Cluster Terminated")
        break
    else:
        logging.info("Waiting 300secs")
        time.sleep(300)

ec2 = boto3.client('ec2',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key)
logging.info("Deleting NEOWAY Security Group")
ec2.delete_security_group(GroupName='NEOWAY')
logging.info("Deleting key pair NEOWAY")
ec2.delete_key_pair(KeyName='NEOWAY')
logging.info("Deleting key pair NEOWAY.pem")
os.unlink(dirpath + '/' + 'NEOWAY.pem')
logging.info("Deleting ClusterId file")
os.unlink(clusteridfile)
logging.info("END")





