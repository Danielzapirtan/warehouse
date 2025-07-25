#! /bin/bash

cd $HOME
sudo apt update
sudo apt install -y git python3-pip
rm -rf warehouse
git clone https://github.com/Danielzapirtan/warehouse.git
cd $HOME/warehouse
pip install -r requirements.txt
pkill -kill streamlit
streamlit run app.py &>/dev/null &
echo Visit http://localhost:8501
