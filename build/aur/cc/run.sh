#!/bin/bash

# gen pkg
python3 builder.py i3-grid
# verify
if [ ! -f ./PKGBUILD ]; then
  echo "Package generation error"
  exit 1
fi
# temp build env
read -p "Test temporary build environment? [Y/n]: " tmpenv
if [[ "$tmpenv" =~ [yY](es)* ]]; then
  mkdir python-i3-grid && cp ./PKGBUILD python-i3-grid/PKGBUILD && cd python-i3-grid
  # build and exit
  makepkg -si && cp ./PKGBUILD ../env_PKGBUILD &&  rm ../PKGBUILD && exit 0
  exit 1 # < error
fi
exit 0
