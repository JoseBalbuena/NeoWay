#!/usr/bin/env bash
set -x -e

JUPYTER_PASSWORD=${1:-"neoway"}
NOTEBOOK_DIR=${2:-"s3://jupyterneowaynotebooksentrevista/"}

# mount home to /mnt
if [ ! -d /mnt/home ]; then
  sudo mv /home/ /mnt/
  sudo ln -s /mnt/home /home
fi

#Install dependences
sudo yum install -y automake fuse fuse-devel gcc-c++ git libcurl-devel libxml2-devel make openssl-devel

# Install conda
wget https://repo.continuum.io/miniconda/Miniconda3-4.3.30-Linux-x86_64.sh -O /home/hadoop/miniconda.sh 
/bin/bash ~/miniconda.sh -b -p $HOME/conda

echo -e '\nexport PATH=$HOME/conda/bin:$PATH' >> $HOME/.bashrc && source $HOME/.bashrc

conda config --set always_yes yes --set changeps1 no
#
#conda install conda=4.2.13

conda config -f --add channels conda-forge
conda config -f --add channels defaults

conda install hdfs3 findspark ujson jsonschema toolz boto3 py4j numpy pandas==0.19.2

# cleanup
rm ~/miniconda.sh
ls /home/hadoop/conda/bin/

##echo bootstrap_conda.sh completed. PATH now: $PATH
export PYSPARK_PYTHON="/home/hadoop/conda/bin/python3.6"
ls -ltrah /home/hadoop/conda/bin/c*

############### -------------- master node -------------- ###############

IS_MASTER=false
if grep isMaster /mnt/var/lib/info/instance.json | grep true;
then
  IS_MASTER=true
  ls -ltrah /home/hadoop/conda/bin/c* 
  ### install dependencies for s3fs-fuse to access and store notebooks
  sudo yum install -y git
  sudo yum install -y libcurl libcurl-devel graphviz
  sudo yum install -y cyrus-sasl cyrus-sasl-devel readline readline-devel gnuplot

  # extract BUCKET and FOLDER to mount from NOTEBOOK_DIR
  NOTEBOOK_DIR="${NOTEBOOK_DIR%/}/"
  BUCKET=$(python -c "print('$NOTEBOOK_DIR'.split('//')[1].split('/')[0])")
  FOLDER=$(python -c "print('/'.join('$NOTEBOOK_DIR'.split('//')[1].split('/')[1:-1]))")

  echo "bucket '$BUCKET' folder '$FOLDER'"

  cd /mnt
  git clone https://github.com/s3fs-fuse/s3fs-fuse.git
  cd s3fs-fuse/
  ls -alrt
  ./autogen.sh
  ./configure
  make
  sudo make install
  sudo su -c 'echo user_allow_other >> /etc/fuse.conf'
  mkdir -p /mnt/s3fs-cache
  mkdir -p /mnt/$BUCKET
  /usr/local/bin/s3fs -o allow_other -o iam_role=auto -o umask=0 -o url=https://s3.us-east-2.amazonaws.com/  -o no_check_certificate -o nonempty -o enable_noobj_cache -o use_cache=/mnt/s3fs-cache $BUCKET /mnt/$BUCKET -o nonempty

  ### Install Jupyter Notebook with conda and configure it.
  echo "installing python libs in master"
  # install
  conda install jupyter

  # install visualization libs
  conda install matplotlib plotly bokeh

  # install scikit-learn stable version
  conda install --channel scikit-learn-contrib scikit-learn==0.18
  ls -ltrah /home/hadoop/conda/bin/c*

  # jupyter configs
  mkdir -p ~/.jupyter
  touch ls ~/.jupyter/jupyter_notebook_config.py
  HASHED_PASSWORD=$(python -c "from notebook.auth import passwd; print(passwd('$JUPYTER_PASSWORD'))")
  echo "c.NotebookApp.password = u'$HASHED_PASSWORD'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.open_browser = False" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.ip = '*'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.notebook_dir = '/mnt/$BUCKET/$FOLDER'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.ContentsManager.checkpoints_kwargs = {'root_dir': '.checkpoints'}" >> ~/.jupyter/jupyter_notebook_config.py

  ### Setup Jupyter deamon and launch it
  cd ~
  echo "Creating Jupyter Daemon"
  echo 'description "Jupyter"' > /home/hadoop/jupyter.conf
  echo "start on runlevel [2345]" >> /home/hadoop/jupyter.conf
  echo "stop on runlevel [016]" >> /home/hadoop/jupyter.conf
  echo "respawn" >> /home/hadoop/jupyter.conf
  echo "respawn limit 0 10" >> /home/hadoop/jupyter.conf
  echo "chdir /mnt/$BUCKET/$FOLDER" >> /home/hadoop/jupyter.conf
  echo "script" >> /home/hadoop/jupyter.conf
  echo "  sudo su - hadoop > /var/log/jupyter.log 2>&1 <<BASH_SCRIPT" >> /home/hadoop/jupyter.conf
  echo '        export PYSPARK_DRIVER_PYTHON="/home/hadoop/conda/bin/jupyter"' >> /home/hadoop/jupyter.conf
  echo '        export PYSPARK_DRIVER_PYTHON_OPTS="notebook --log-level=INFO"' >> /home/hadoop/jupyter.conf
  echo "        export PYSPARK_PYTHON=/home/hadoop/conda/bin/python3.6" >> /home/hadoop/jupyter.conf
  echo "        export JAVA_HOME="/etc/alternatives/jre"" >> /home/hadoop/jupyter.conf
  echo "        pyspark" >> /home/hadoop/jupyter.conf
  echo "  BASH_SCRIPT" >> /home/hadoop/jupyter.conf
  echo "end script" >> /home/hadoop/jupyter.conf

  sudo mv /home/hadoop/jupyter.conf /etc/init/
  sudo chown root:root /etc/init/jupyter.conf

  sudo initctl reload-configuration

  # start jupyter daemon
  echo "Starting Jupyter Daemon"
  sed -i 's/*/0.0.0.0/g' /mnt/home/hadoop/.jupyter/jupyter_notebook_config.py
  sudo initctl start jupyter

  #Install JupyterHUB
  curl --silent --location https://rpm.nodesource.com/setup_10.x | sudo bash -
  sudo yum -y install nodejs
  sudo npm install -g configurable-http-proxy
  conda install -c conda-forge jupyterhub
  sudo ln -sf /mnt/home/hadoop/conda/bin/jupyterhub /usr/bin/
  sudo ln -sf /mnt/home/hadoop/conda/bin//jupyterhub-singleuser /usr/bin/

  #Criando alguns usuarios de teste
  sudo useradd neoway
  sudo bash -c "echo neoway:neoway | chpasswd"
  sudo useradd whisky
  sudo bash -c "echo whisky:neoway | chpasswd"
  mkdir /mnt/jupyterhub

  #Changing Pass of hadoop
  sudo bash -c "echo hadoop:neoway | chpasswd"

  jupyterhub --generate-config
  mv jupyterhub_config.py /mnt/jupyterhub/

  #KEEP env Variables in JupyterHUB
  echo "import os" >> /mnt/jupyterhub/jupyterhub_config.py
  echo "for var in os.environ:" >> /mnt/jupyterhub/jupyterhub_config.py
  echo "    c.Spawner.env_keep.append(var)" >> /mnt/jupyterhub/jupyterhub_config.py

  #Criando script de startup
  echo 'description "JupyterHub"' > /home/hadoop/jupyterhub.conf
  echo 'start on runlevel [2345]' >> /home/hadoop/jupyterhub.conf
  echo 'stop on runlevel [016]' >> /home/hadoop/jupyterhub.conf
  echo 'respawn' >> /home/hadoop/jupyterhub.conf
  echo 'respawn limit 0 10' >> /home/hadoop/jupyterhub.conf
  echo 'chdir /mnt/jupyterhub' >> /home/hadoop/jupyterhub.conf
  echo 'script' >> /home/hadoop/jupyterhub.conf
  echo '  sudo su - hadoop > /var/log/jupyterhub.log 2>&1 <<BASH_SCRIPT' >> /home/hadoop/jupyterhub.conf
  echo '        export PYSPARK_DRIVER_PYTHON="/home/hadoop/conda/bin/jupyter"' >> /home/hadoop/jupyterhub.conf
  echo '        export PYSPARK_DRIVER_PYTHON_OPTS="notebook --log-level=INFO"' >> /home/hadoop/jupyterhub.conf
  echo '        export PYSPARK_PYTHON=/home/hadoop/conda/bin/python3.6' >> /home/hadoop/jupyterhub.conf
  echo '        export JAVA_HOME="/etc/alternatives/jre"' >> /home/hadoop/jupyterhub.conf
  echo '        export JAVA_HOME="/etc/alternatives/jre"' >> /home/hadoop/jupyterhub.conf
  echo '        export NOTEBOOK_DIR="/mnt/jupyterneowaynotebooksentrevista"' >> /home/hadoop/jupyterhub.conf
  echo '        export NODE_PATH="/usr/lib/node_modules"' >> /home/hadoop/jupyterhub.conf
  echo '        sudo jupyterhub --port=9443 --config /mnt/jupyterhub/jupyterhub_config.py' >> /home/hadoop/jupyterhub.conf
  echo '  BASH_SCRIPT' >> /home/hadoop/jupyterhub.conf
  echo 'end script' >> /home/hadoop/jupyterhub.conf

  sudo mv /home/hadoop/jupyterhub.conf /etc/init/
  sudo chown root:root /etc/init/jupyterhub.conf

  sudo initctl reload-configuration

  # start jupyterhub daemon
  echo "Starting Jupyterhub Daemon"
  sudo initctl start jupyterhub

fi
