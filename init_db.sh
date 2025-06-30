#! /bin/bash

FOLDER=./WarehouseDB
ALT_FOLDER=.
FILENAME='db.json'

if test -f $FOLDER/$FILENAME; then
   true
else
    mkdir -p $FOLDER
    cp -a $ALT_FOLDER/$FILENAME $FOLDER
fi

apt install python3-pip
pip install -r requirements.txt