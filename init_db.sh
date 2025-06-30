#! /bin/bash

apt install python3-pip
pip install -r requirements.txt
${WAREHOUSEDB:="{}"}
export WAREHOUSEDB
echo "WAREHOUSEDB=$WAREHOUSEDB"
