#!/bin/bash

cp -r ../i3grid .
python3 main_test.py
rm -rf ./i3grid
rm -rf ./__pycache__
