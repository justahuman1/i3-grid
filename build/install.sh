#!/bin/bash

checkExistingFolder() {
    if [ ! -d "$1" ]; then
        mkdir $1
    else
        read -p "i3-grid dotfiles already installed. Reinstall? [y/N]: " reins
        if [[ $reins =~ [yY](es)* ]]; then
            :
        else
            echo "Cancelled reinstallation"
            exit 0
        fi
    fi
}
if [ -d "$HOME/.config" ]; then
    _APP_LOC="$HOME/.config/i3grid"
    _APP_LOC=$(echo -n "${XDG_CONFIG_HOME:-$HOME/.config}")
    _RC="i3gridrc"
else
    _APP_LOC="$HOME"
    _RC=".i3gridrc"
fi
checkExistingFolder $_APP_LOC
curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/.i3gridrc > "$_APP_LOC/$_RC"
echo "Installation complete. RC File location:"
echo -e "\t$_APP_LOC/$RC"
echo -e "======================================\n"

read -p "Download the Rofi frontend? [y/N]: " insFE
if [[ $insFE =~ [yY](es)* ]]; then
    curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/manager.sh > "$_APP_LOC/manager.sh"
    curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/matrix.rasi > "$_APP_LOC/matrix.rasi"
    chmod +x "$_APP_LOC/manager.sh"
    echo "Installed rofi frontend. Location:"
    echo -e "\t$_APP_LOC/$RC\n"
fi
echo "======================================"
echo "[i3-grid] Configuration completed"
