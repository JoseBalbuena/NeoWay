# SOLUÇÃO

Para resolver o problema foram criados dois scripts python que utilizam a livraria python boto3, Esses dois scripts precisam ser agendados na cron de alguma máquina Linux. Os scripts basicamente criam e destroem um cluster EMR. O cluster EMR é instalado com Hadoop Spark e Ganglia para monitoramento.

A solucao utiliza as credenciais enviadas pela NeoWay na AWS.

## Pre-requisitos para execucao dos scripts
1. Linux 
2. Python3.6
3. Modulo python boto3 
4. Bucket "jupyterneowaynotebooksentrevista" na regiao us-east2 (US Ohio), já criado na minha conta pessoal da AWS, aqui serao armazenados os "notebooks" do Jupyter. https://s3.console.aws.amazon.com/s3/buckets/jupyterneowaynotebooksentrevista/?region=sa-east-1&tab=overview
5. Bootstrap script para instalação do Jupyter e JupyterHUB. Esse script irá instalar o Jupyter e JupyterHUB no cluster spark.Já criado na minha conta pessoal da AWS. https://s3.us-east-2.amazonaws.com/bootstrapjupyterneoway/bootstrap-jupyter.sh

## Script CreateClusterEMRSpark.py
O script lê o arquivo clusterconfig.cnf, onde existe a possibilidade de setar diferentes opcoes de configuracao, e cria um cluster EMR.
```sh
[AWSCREDENTIALS]
aws_access_key_id=XXXXXXXXXXXXXXXXXXXXXX
aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
region_name=us-east-2
[CLUSTERSPARK]
client_network=0.0.0.0/0
instance-type=m4.large
number-slaves=2
```
As chaves de acesso foram escondidas aqui no github por razoes de seguranca. 
A variavél client_network, é onde podemos setar a rede interna do cliente, e para a qual serão liberados os acessos SSH. Por default coloquei 0.0.0.0/0

A sequencia do script é a seguinte:

1. Lê as credenciais/opções do arquivo clusterconfig.cnf.
2. Cria/Salva uma chave NEOWAY.PEM
3. Cria um security group NEOWAY, com as permissões de acesso para a rede do cliente.
4. Cria o cluster EMR, com a chave NEOWAY, Security Group Adicional NEOWAY, Hadoop, Spark e Ganglia e bootstrap script bootstrap-jupyter.sh.
5. Espera terminar a criação, status "WAITING" e printa o endereço url do master, com as portas abertas indicando a qual aplicação pertence cada porta.
6. Armazena o ClusterId no arquivo de texto clusterid.

O script irá gera um log no formato CreateClusterEMRSpark.log.YYYYMMDD, é possivél debugar o script trocando de level=logging.INFO para level=logging.DEBUG.


## Script TerminateClusterEMRSpark.py
Esse script finaliza o Cluster EMR previamente criado. A sequencia é:

1. Lê as credenciais/opções do arquivo clusterconfig.cnf.
2. Lê o ClusterId do arquivo clusterid.
3. Termina o Cluster EMR.
4. Espera Terminar o Cluster.
5. Quando o Cluster estar no status "TERMINATED", apaga a chave NEOWAY e o security group NEOWAY.
6. Apaga o arquivo clusterid.

O script irá gera um log no formato TerminateClusterEMRSpark.log.YYYYMMDD, é possivél debugar o script trocando de level=logging.INFO para level=logging.DEBUG.

# CENÁRIO DE TESTE
Para testar os scripts criar uma VM Ubuntu 18.04 EC2, aproveitando a conta da AWS, ela já vem cm python 3.6

Instalando pip3 e boto3.
```sh
sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install unzip
sudo pip3 install boto3
```

Criando pasta NeoWay e baixando os arquivos do github. 
```sh
mkdir NeoWay
cd NeoWay
wget https://github.com/JoseBalbuena/NeoWay/archive/master.zip
```
Unzipping
```sh
ubuntu@ip-172-31-43-211:~/NeoWay$ unzip master.zip 
Archive:  master.zip
6f6179ac9241856103a66e6c41de7305f4f5b010
   creating: NeoWay-master/
  inflating: NeoWay-master/CreateClusterEMRSpark.py  
  inflating: NeoWay-master/README.md  
  inflating: NeoWay-master/TerminateClusterEMRSpark.py  
  inflating: NeoWay-master/bootstrap-jupyter.sh  
  inflating: NeoWay-master/clusterconfig.cnf  
ubuntu@ip-172-31-43-211:~/NeoWay$ 
```
Inserir as credencias de acesso no arquivo clusterconfig.cnf.
```sh
aws_access_key_id=XXXXXXXXXXXXXXXXXXXXXXXXX
aws_secret_access_key=YYYYYYYYYYYYYYYYYYYYYYYYYYYY
```
Dar permissão de execução:
```sh
ubuntu@ip-172-31-43-211:~/NeoWay$ cd NeoWay-master/
ubuntu@ip-172-31-43-211:~/NeoWay/NeoWay-master$ chmod +x CreateClusterEMRSpark.py 
ubuntu@ip-172-31-43-211:~/NeoWay/NeoWay-master$ chmod +x TerminateClusterEMRSpark.py 
ubuntu@ip-172-31-43-211:~/NeoWay/NeoWay-master$ 
```
Inserir em cron, horarios 07, e 19hrs
```sh
0 7 * * * /home/ubuntu/NeoWay/NeoWay-master/CreateClusterEMRSpark.py
0 19 * * * /home/ubuntu/NeoWay/NeoWay-master/TerminateClusterEMRSpark.py
```
Caso queira testar sem esperar a cron, os scripts podem ser executados manualmente, lenbrado que a saída irá ser armazenada no arquivo log, para poder acompanhar precisa abrir outra sessão via terminal e enviar um tail -f arquivo_log.log.YYYYMMDD

# LOG DE EXECUÇÃO
Script de criação:
```sh
ubuntu@ip-172-31-21-20:~/NeoWay/NeoWay-master$ tail -f CreateClusterEMRSpark.log.20181129 
19:46:01,835 root INFO Parsing config file /home/ubuntu/NeoWay/NeoWay-master/clusterconfig.cnf 
19:46:01,835 root INFO Creating key pair NEOWAY
19:46:01,993 root INFO Saving key pair
19:46:01,993 root INFO Changing Permission on NEOWAY.pem file
19:46:01,993 root INFO Criando Security Group NEOWAY
19:46:02,369 root INFO Criando Cluster EMR
19:46:02,703 root INFO ClusterID: j-OKFWPEPYY21H , DateCreated: Thu, 29 Nov 2018 19:46:02 GMT , RequestId: 66f55100-f40f-11e8-acd8-a772f2c95706
19:46:02,703 root INFO Writing Cluster Id in file /home/ubuntu/NeoWay/NeoWay-master/clusterid
19:46:02,703 root INFO Waiting ...
19:46:02,777 root INFO Waiting 300sec
19:51:03,51 root INFO Waiting 300sec
19:56:03,300 root INFO Waiting 300sec
20:01:03,537 root INFO Cluster Started
20:01:03,537 root INFO Jupyter NoteBook: http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:8888 (password:neoway)
20:01:03,538 root INFO JupyterHUB http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:9443 (user:hadoop/pass:neoway)
20:01:03,538 root INFO Ganglia Monitoring http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com
20:01:03,538 root INFO Spark History Jobs http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:18080
20:01:03,538 root INFO END
```
O log mostra os endereços web do Jupyer, JupyterHUB, Ganglia e o Spark History

1. Jupyter NoteBook: http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:8888 (password:neoway)
2. JupyterHUB http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:9443 (user:hadoop/pass:neoway)
3. Ganglia Monitoring http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com
4. Spark History Jobs http://ec2-52-14-36-20.us-east-2.compute.amazonaws.com:18080

Script de terminação:
```sh
ubuntu@ip-172-31-21-20:~/NeoWay/NeoWay-master$ tail -f TerminateClusterEMRSpark.log.20181129 
20:11:01,813 root INFO ------------------------------------------------------------------------
20:11:01,813 root INFO Start 20181129201101
20:11:01,813 root INFO Script para criar cluster spark
20:11:01,813 root INFO -----------------------------------------------------------------------------
20:11:01,813 root INFO Parsing config file /home/ubuntu/NeoWay/NeoWay-master/clusterconfig.cnf 
20:11:01,814 root INFO Terminating Cluster EMR
20:11:01,842 root INFO Reading ClusterId from file /home/ubuntu/NeoWay/NeoWay-master/clusterid
20:11:02,76 root INFO Waiting ...
20:11:02,153 root INFO Waiting 300secs
20:16:02,340 root INFO Cluster Terminated
20:16:02,370 root INFO Deleting NEOWAY Security Group
20:16:02,646 root INFO Deleting key pair NEOWAY
20:16:02,708 root INFO Deleting key pair NEOWAY.pem
20:16:02,708 root INFO Deleting ClusterId file
20:16:02,708 root INFO END
```
