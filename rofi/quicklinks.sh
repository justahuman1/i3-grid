#!/usr/bin/env bash

rofi_command="rofi -theme matrix.rasi"

# Links
google=""
facebook=""
twitter=""
github=""
mail=""
youtube=""

# Variable passed to rofi
options="$google\n$facebook\n$twitter\n$github\n$mail\n$youtube"

chosen="$(echo -e "$options" | $rofi_command -p "Open In  :  Firefox" -dmenu -selected-row 0)"
case $chosen in
    $google)
        echo "0"
        ;;
    $facebook)
        echo "1"
        ;;
    $twitter)
        echo "2"
        ;;
    $github)
        echo "3"
        ;;
    $mail)
        echo "4"
        ;;
    $youtube)
        echo "5"
        ;;
esac

