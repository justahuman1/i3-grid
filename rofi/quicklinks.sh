#!/usr/bin/env bash

app_abs_path="/home/sai/Code/temp/quadrant3"
# Set rofi env vars for rasi config
# Corresponds to grid numbers..
export COLS=2
export LINES=2
rofi_command="rofi -i -theme $app_abs_path/rofi/style_normal.rasi -multi-select"

# Column and row chooser possibility
join() { local IFS="$1"; shift; echo "$*"; }

# We can use a python function to dynamically generate the
# grid for different canvases on the fly. Or maybe a small
# awk code to swap every non != len(lines) number.
grid=(
    1
    3   # Swap due to rofi options folding
    2
    4
    "C" # Custom Percentage, center window (ofc, you can override otf)
    "D" # Use default rc file rows and col nums to create grid and use input num as snap target
    "R" # Reset to i3 default center (75% screen)
    "X" # Custom row, col, target parsing
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
# Path to the src python file
src_file="$app_abs_path/floatwm.py"

if [[ "$len" -gt "1" ]]; then
    # if multi select

    # parse rofi multiselect
    declare -a arr
    arr=( $(echo $chosen | awk '{split($0,a," ")} END {for(n in a){ print a[n] }}') )
    if [ "$len" == "3" ]; then
        if [ "${arr[0]}" == "1" ] || [ "${arr[0]}" == "3" ]; then
            if [ ${arr[1]} == "3" ] || [ "${arr[1]}" == "1" ]; then
                # Left half align
                python  $src_file \
                    float resize snap \
                    --cols 2 --rows 1 --target 1
            fi
        fi
        if [ "${arr[0]}" == "2" ] || [ "${arr[0]}" == "4" ]; then
            if [ ${arr[1]} == "4" ] || [ "${arr[1]}" == "2" ]; then
                # Right half align
                python  $src_file \
                    float resize snap \
                    --cols 2 --rows 1 --target 2
            fi
        fi
        if [ "${arr[0]}" == "1" ] || [ "${arr[0]}" == "2" ]; then
            if [ ${arr[1]} == "2" ] || [ "${arr[1]}" == "1" ]; then
                # Top half align
                python  $src_file \
                    float resize snap \
                    --cols 1 --rows 2 --target 1
            fi
        fi
        if [ "${arr[0]}" == "3" ] || [ "${arr[0]}" == "4" ]; then
            if [ ${arr[1]} == "4" ] || [ "${arr[1]}" == "3" ]; then
                # Bottom half align
                python  $src_file \
                    float resize snap \
                    --cols 1 --rows 2 --target 2
            fi
        fi
    elif [ "$len" == "7" ]; then
        echo "Full screen?"
    fi

    exit
elif [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # whatever you want to do when arr doesn't contain value
    echo "Error: Element Out of grid"
    exit
fi

if [[ "$chosen"  ==  "0" ]]; then
    python  $src_file float resize snap --target 0
elif [[ "$chosen"  ==  "C" ]]; then
    p="$($rofi_command -dmenu -selected-row 0)"
    python $src_file csize --perc=$p
elif [[ "$chosen"  ==  "D" ]]; then
    target="$($rofi_command -dmenu -selected-row 0)"
    python $src_file float resize snap --target $target
elif [[ "$chosen"  ==  "R" ]]; then
    python $src_file float reset
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
fi

