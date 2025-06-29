#! /bin/bash

FOLDER=/content/drive/MyDrive/WarehouseDB
ALT_FOLDER=/content/warehouse
FILENAME='db.json'

if test -f $FOLDER/$FILENAME
    true
else
    cp -a ALT_FOLDER/$FILENAME $FOLDER
fi