#! /bin/bash

cd $HOME
sudo apt update
sudo apt install git
git clone https://github.com/Danielzapirtan/warehouse.git
cd warehouse
FOLDER=/home/userland/WarehouseDB
ALT_FOLDER=./warehouse
FILENAME='db.json'
if test -f $FOLDER/$FILENAME; then
   true
else
    mkdir -p $FOLDER
    cp -a $ALT_FOLDER/$FILENAME $FOLDER
fi
sudo apt install python3-pip
pip install -r requirements.txt
python3 app.py &>/dev/null &
echo "Visit localhost:7860 in your browser"

