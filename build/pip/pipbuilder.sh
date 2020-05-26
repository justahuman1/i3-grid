#!/bin/bash

cp ../../i3-grid -r .
cd i3-grid
python3 setup.py sdist bdist_wheel
python3 -m twine upload --repository pypi dist/*
cd ..
rm -rf i3-grid
