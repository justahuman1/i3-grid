#!/usr/bin/env bash

#   GitHub: justahuman1
#   URL: https://github.com/justahuman1
#   License: GPL-3.0
#     Copyright (C) 2020 Sai Valla
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.

#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.

#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

# ---- Rofi Frontend ----
# src file absolute path
app_abs_path="/home/sai/Code/FullApps/quadrant"
# Set rofi env vars for rasi config
# Corresponds to grid numbers..
export COLS=2
export LINES=2
rofi_command="rofi -i -theme $app_abs_path/rofi/matrix.rasi -multi-select"

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
    "X" # Custom col, row, target parsing
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
chosen="$(echo -e "$options" | $rofi_command -dmenu -p "Grid:" -selected-row 0)"
len=${#chosen}
# Path to the src python file
src_file="$app_abs_path/i3-grid/floatwm.py"

if [[ "$len" -gt "1" ]]; then
    # if multi select
    # parse rofi multiselect
    declare -a arr
    arr=( $(echo $chosen | awk '{split($0,a," ")} END {for(n in a){ print a[n] }}') )
    if [ "$len" == "3" ]; then
        if [ "${arr[0]}" == "1" ] && [ "${arr[1]}" == "3" ]; then
            # Left half align
            python  $src_file \
                float resize snap \
                --cols 2 --rows 1 --target 1
        elif [ "${arr[0]}" == "2" ] && [ "${arr[1]}" == "4" ]; then
            # Right half align
            python  $src_file \
                float resize snap \
                --cols 2 --rows 1 --target 2
        elif [ "${arr[0]}" == "1" ] && [ "${arr[1]}" == "2" ]; then
            # Top half align
            python  $src_file \
                float resize snap \
                --cols 1 --rows 2 --target 1
        elif [ "${arr[0]}" == "3" ] && [ "${arr[1]}" == "4" ]; then
            # Bottom half align
            python  $src_file \
                float resize snap \
                --cols 1 --rows 2 --target 2
        fi
    elif [ "$len" == "7" ]; then
        echo "Full screen?"
        python  $src_file \
            float resize snap \
            --cols 1 --rows 1 --target 1
    fi

    exit
elif [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # whatever you want to do when arr doesn't contain value
    echo "Error: Element Out of grid"
    python $src_file -h
    exit
fi

# Single select options (These can also be combined!)
if [[ "$chosen"  ==  "0" ]]; then
    python  $src_file float resize snap --target 0
elif [[ "$chosen"  ==  "C" ]]; then
    p="$($rofi_command -dmenu -p "% -" -selected-row 0)"
    python $src_file csize --perc=$p
elif [[ "$chosen"  ==  "D" ]]; then
    target="$($rofi_command -dmenu -p 'Target:' -selected-row 0)"
    python $src_file float resize snap --target $target
elif [[ "$chosen"  ==  "R" ]]; then
    python $src_file float reset
elif [[ "$chosen"  ==  "X" ]]; then
    custom="$($rofi_command -dmenu -p "c r t:" -selected-row 0)"
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
    python $src_file float snap --cols $COLS --rows $LINES --target $chosen
fi

