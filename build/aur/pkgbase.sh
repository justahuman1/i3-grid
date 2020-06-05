#!/bin/bash

git clone ssh://aur@aur.archlinux.org/python-i3-grid
cp ./PKGBUILD ./python-i3-grid
cd python-i3-grid && makepkg --printsrcinfo > .SRCINFO

echo "Updated i3-grid AUR Repo. Add the files and push commit to AUR:"
echo -e "\tgit add PKGBUILD .SRCINFO\n\tgit commit -m <commitName>\n\tgit push "
