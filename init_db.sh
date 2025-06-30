#! /bin/bash

apt install python3-pip
pip install -r requirements.txt
if [ "x$WAREHOUSEDB" = "x" ]; then
    WAREHOUSEDB="{}"
fi
export WAREHOUSEDB
echo "WAREHOUSEDB=$WAREHOUSEDB"
