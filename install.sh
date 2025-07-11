#! /bin/bash

cd $HOME
sudo apt install git python3-pip
pip install -r requirements.txt
rm -rf warehouse
git clone https://github.com/Danielzapirtan/warehouse.git
cd warehouse
streamlit run app.py &>/dev/null &
echo Visit http://localhost:8501
