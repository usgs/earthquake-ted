# ted
Tweet Earthquake Detector source code repository


Install Notes
1) if miniconda is not already installed then first do
  curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o Miniconda3-latest-Linux-x86_64.sh
  bash Miniconda3-latest-Linux-x86_64.sh (follow prompts)
  source .bashrc
  conda config --add channels conda-forge

  conda install packages as needed

2) set up for SSL (may have to happen before step 1) - instructions at https://gitlab.cr.usgs.gov/mhearne/install-ssl

3) install this project (ted trigger code)
    ssh into TED Dev server
    cd /home/ted/tedapp
    sudo su ted 
    git clone https://github.com/mhearne-usgs/ted.git
    cd ted
    ./install.sh
    
