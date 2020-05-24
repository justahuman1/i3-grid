#!/bin/bash

cp -r ../i3grid .
# cd i3grid
python3 main.py
# cd ..
rm -rf ./i3grid
