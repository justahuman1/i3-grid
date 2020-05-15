#!/usr/bin/env bash

app_abs_path="/home/sai/Code/temp/quadrant3"
# Set rofi env vars for rasi config
# Corresponds to grid numbers..
export COLS=2
export LINES=2
rofi_command="rofi -theme $app_abs_path/rofi/style_normal.rasi -multi-select"



# Column and row chooser possibility
# chosen="$(echo -e "$options" | $rofi_command -P "Mew?" -dmenu )"

join() { local IFS="$1"; shift; echo "$*"; }

# We can use a python function to dynamically generate the
# grid for different canvases on the fly. Or maybe a small
# awk code to swap every non != len(lines) number.
grid=(
    1
    3   # Swap due to rofi options folding
    2
    4
    "L" # Left
    "T" # Top
    "R" # Right
    "B" # Bottom
    "C" # Center (75% screen)
    "X" # Custom row, col, target parsing
    "P" # Custom Percentage, center window (ofc, you can override otf)
    0
)
# Without the swap, we can make it dynamic and allow on the fly
# grids. We need to change our python library to adjust for this.
# Or if there is a flexbox column-row numbering is possible with rasi (css),
# that would be the best option.
options=""
for i in ${grid[*]}; do
    options="${options}${i}\n"
done

# grid options passed to rofi
chosen="$(echo -e "$options" | $rofi_command -dmenu -selected-row 0)"
len=${#chosen}

if [[ "$len" -gt "1" ]]; then
    # if multi select

    # parse rofi multiselect
    arr=$(echo $chosen | awk '{split($0,a," ")} END {for(n in a){ print a[n] }}')
    echo "arr:${arr[*]}"
    echo "la len:$len"
    if [ "$len" == "3" ]; then
        echo "Threeing huh"
    elif [ "$len" == "7" ]; then
        echo "Full screen?"
    fi

    exit
elif [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # whatever you want to do when arr doesn't contain value
    echo "Error: Element Out of grid"
    exit
fi
echo fail
exit

# Path to the src python file
src_file="$app_abs_path/floatwm.py"
if [[ "$chosen"  ==  "0" ]]; then
    python  $src_file float resize snap --target 0
elif [[ "$chosen"  ==  "L" ]]; then
    python  $src_file float resize snap --cols 2 --rows 1 --target 1
elif [[ "$chosen"  ==  "R" ]]; then
    python $src_file float resize snap --cols 2 --rows 1 --target 2
elif [[ "$chosen"  ==  "T" ]]; then
    python $src_file float resize snap --cols 1 --rows 2 --target 1
elif [[ "$chosen"  ==  "B" ]]; then
    python $src_file float resize snap --cols 1 --rows 2 --target 2
elif [[ "$chosen"  ==  "C" ]]; then
    python $src_file float reset
elif [[ "$chosen"  ==  "P" ]]; then
    p="$($rofi_command -dmenu -selected-row 0)"
    python $src_file csize --perc=$p
elif [[ "$chosen"  ==  "X" ]]; then
    custom="$($rofi_command -dmenu -selected-row 0)"
    IFS=' ' read -ra r_c_t <<< "$custom"
    if [[ "${#r_c_t[@]}" != "3" ]]; then
        echo "Incorrect Argument Length (Need Row, Col, Target)"
        exit
    fi
    python $src_file \
      float resize snap  \
      --cols ${r_c_t[0]} --rows ${r_c_t[1]}  \
      --target ${r_c_t[2]}
else
    python $src_file float resize snap --cols 2 --rows 2 --target $chosen
fi

