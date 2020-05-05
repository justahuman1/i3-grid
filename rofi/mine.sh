#!/bin/bash

printHelpMenu(){
    echo "{}"
}

main() {
    case "$COMMAND" in
    '')
        echo "No arguments provided..." && printHelpMenu
    ;;
    "help")
        printHelpMenu
    ;;
    "1")
        i3-msg resize width 25ppt height 50ppt
        # i3-msg move c
    ;;
    *)
        echo "Command Not Found" && printHelpMenu
    ;;
    esac
}

main
