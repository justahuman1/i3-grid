#!/bin/bash

# gen pkg
python3 builder.py i3-grid
# verify
if [ ! -f ./PKGBUILD ]; then
    echo "Package generation error"
    exit 1
fi
# temp build env
mkdir tmp && cp ./PKGBUILD tmp/PKGBUILD && cd tmp
# build and exit
makepkg -si && cp ./PKGBUILD ../tmp_PKGBUILD && exit 0
exit 1
