#!/bin/bash

cp ../../i3-grid -r .
cd i3-grid
python3 setup.py sdist bdist_wheel
read -p "Test Pypy or Pypy? [T/P]: " dest
if [[ $dest =~ [pP]* ]]; then
  dest="pypi"
else
  dest="testpypi"
fi
python3 -m twine upload --repository $dest dist/*
cd ..
rm -rf i3-grid
