#!/bin/bash

# gen pkg
python3 builder.py i3-grid
# verify
if [ ! -f ./PKGBUILD ]; then
    echo "package gen error"
    exit
fi

# temp build env
mkdir tmp
cp ./PKGBUILD tmp/PKGBUILD
cd tmp

