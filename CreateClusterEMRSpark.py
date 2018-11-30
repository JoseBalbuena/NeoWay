#!/usr/bin/python3.6
#####################################################################################################################################
# NeoWay Interview
# Script to create a EMR Cluster
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
abspath = os.path.abspath(__file__)
dirpath=os.path.dirname(abspath)


configfile=dirpath + '/clusterconfig.cnf'
clusteridfile=dirpath + '/clusterid'
DataLog = datetime.now().strftime("%Y%m%d")
Log=dirpath + '/CreateClusterEMRSpark.log.' + DataLog
print(Log)
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

#Create KEY PAIR
logging.info("Creating key pair NEOWAY")
ec2 = boto3.client('ec2',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key)
response = ec2.create_key_pair(KeyName='NEOWAY')

#Save KEY PAIR
logging.info("Saving key pair")
with open(dirpath + '/' + 'NEOWAY.pem','w') as fh:
    fh.write(response['KeyMaterial'])

#Change Permission
logging.info("Changing Permission on NEOWAY.pem file")
os.chmod(dirpath + '/' + 'NEOWAY.pem', 0o400)

logging.info("Criando Security Group NEOWAY")
response = ec2.create_security_group(GroupName='NEOWAY',
                                         Description='Acesso SSH desde Rede do Cliente',
                                         )
security_group_id = response['GroupId']
print('Security Group Created %s ' % security_group_id)
data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},
            {'IpProtocol': 'tcp',
             'FromPort': 8080,
             'ToPort': 8080,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},
            {'IpProtocol': 'tcp',
             'FromPort': 18080,
             'ToPort': 18080,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},
            {'IpProtocol': 'tcp',
             'FromPort': 8888,
             'ToPort': 8888,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},
            {'IpProtocol': 'tcp',
             'FromPort': 9443,
             'ToPort': 9443,
             'IpRanges': [{'CidrIp': config['CLUSTERSPARK']['client_network']}]},

        ])


logging.info("Criando Cluster EMR")
client = boto3.client('emr',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key)



emrcluster = client.run_job_flow(
    Name='EMR Cluster with Boto',
    ReleaseLabel='emr-5.19.0',
    LogUri='s3://neowayjose/logs/',
    Instances={
        'InstanceGroups': [
            {
                'Name': "Master nodes",
                'Market': 'ON_DEMAND',
                'InstanceRole': 'MASTER',
                'InstanceType': config['CLUSTERSPARK']['instance-type'],
                'InstanceCount': 1,
            },
            {
                'Name': "Slave nodes",
                'Market': 'ON_DEMAND',
                'InstanceRole': 'CORE',
                'InstanceType': config['CLUSTERSPARK']['instance-type'],
                'InstanceCount': int(config['CLUSTERSPARK']['number-slaves']),
            }
        ],
        'Ec2KeyName': 'NEOWAY',
        'KeepJobFlowAliveWhenNoSteps': True,
        'TerminationProtected': False,
        'AdditionalMasterSecurityGroups': [
                security_group_id,
            ],
        'AdditionalSlaveSecurityGroups': [
                security_group_id,
            ],
    },
    BootstrapActions=[
                     {'Name':'Install Jupyter notebook',
                      'ScriptBootstrapAction': { 
                           'Path':'s3://bootstrapjupyterneoway/bootstrap-jupyter.sh',
                           'Args':[]
                                               } 
                       },
                      ],
    Applications=[{'Name':'Hadoop'},{'Name':'Spark'},{'Name':'Ganglia'}],
    VisibleToAllUsers=True,
    JobFlowRole='EMR_EC2_DefaultRole',
    ServiceRole='EMR_DefaultRole',
    Tags=[
        {
            'Key': 'Name',
            'Value': 'EMR with Boto',
        },
        {
            'Key': 'TerminationVal',
            'Value': 'OK',
        },
    ],
)

logging.info('ClusterID: %s , DateCreated: %s , RequestId: %s' % (emrcluster['JobFlowId'],emrcluster['ResponseMetadata']['HTTPHeaders']['date'],emrcluster['ResponseMetadata']['RequestId']))
clusterid=emrcluster['JobFlowId']

logging.info("Writing Cluster Id in file %s" % clusteridfile)
with open(clusteridfile,'w') as fh:
    fh.write(emrcluster['JobFlowId'])
logging.info("Waiting ...")

while True:
    client = boto3.client('emr',region_name=region,aws_access_key_id=key_id,aws_secret_access_key=access_key) 
    response=client.describe_cluster(ClusterId=clusterid)
    status=response['Cluster']['Status']['State']
    if status=='WAITING':
        logging.info("Cluster Started")
        masternode=response['Cluster']['MasterPublicDnsName']
        logging.info("Jupyter NoteBook: http://%s:8888 (password:neoway)" % masternode)
        logging.info("JupyterHUB http://%s:9443 (user:hadoop/pass:neoway)" % masternode)
        logging.info("Ganglia Monitoring http://%s" % masternode)
        logging.info("Spark History Jobs http://%s:18080" % masternode)
        break
    elif status=='TERMINATED':
        logging.info("Failed to Create Cluster")
        break
    else:        
        logging.info("Waiting 300sec")
        time.sleep(300)

logging.info("END")


