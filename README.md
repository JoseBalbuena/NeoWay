# SOLUCAO

Para resolver o problema foram criados dois scripts python que utilizam a livraria python boto3, Esses dois scripts precisam ser agendados na cron de alguma máquina Linux. Os scripts basicamente criam e destroem um cluster EMR. O cluster EMR é instalado com Hadoop Spark e Ganglia para monitoramento.

A solucao utiliza as credenciais enviadas pela NeoWay na AWS.

## Pre-requisitos para execucao dos scripts
1. Linux 
2. Python3.6
3. Modulo python boto3 
4. Bucket "jupyterneowaynotebooksentrevista" na regiao us-east2 (US Ohio), já criado na minha conta pessoal da AWS, aqui serao armazenados os "notebooks" do Jupyter. https://s3.console.aws.amazon.com/s3/buckets/jupyterneowaynotebooksentrevista/?region=sa-east-1&tab=overview
5. Bootstrap script para instalação do Jupyter. Esse script irá instalar o Jupyter no cluster spark.Já criado na minha conta pessoal da AWS. https://s3.us-east-2.amazonaws.com/bootstrapjupyterneoway/bootstrap-jupyter.sh

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

O script irá gera um log no formato CreateClusterEMRSpark.log.YYYYMMDD

## Script TerminateClusterEMRSpark.py
Esse script finaliza o Cluster EMR previamente criado. A sequencia é:

1. Lê as credenciais/opções do arquivo clusterconfig.cnf.
2. Lê o ClusterId do arquivo clusterid.
3. Termina o Cluster EMR.
4. Espera Terminar o Cluster.
5. Quando o Cluster estar no status "TERMINATED", apaga a chave NEOWAY e o security group NEOWAY.
6. Apaga o arquivo clusterid.

O script irá gera um log no formato TerminateClusterEMRSpark.log.YYYYMMDD

# CENARIO DE TESTE
Para testar os scripts criei uma VM Ubuntu 18.04 EC2, já vem cm python 3.6, na conta proporcionada pela NeoWay. A chave é MAQUINATESTE.pem

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
Caso queira testar sem esperar a cron, os scripts podem ser executados manualmente, lenbrado que a saída irá ser armazenada no arquivo log.





