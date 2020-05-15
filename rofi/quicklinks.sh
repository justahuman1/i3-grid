#!/usr/bin/env bash

rofi_command="rofi -theme rofi/style_normal.rasi"


# Column and row chooser possibility
# chosen="$(echo -e "$options" | $rofi_command -P "Mew?" -dmenu )"

join() { local IFS="$1"; shift; echo "$*"; }

grid=(
    1
    3   # Swap due to rofi options folding
    2
    4
    0
    "L" # Left
    "R" # Right
    "T" # Top
    "B" # Bottom
    "C" # Center (75% screen)
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

if [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # whatever you want to do when arr doesn't contain value
    echo "Error: Element Out of grid"
    exit
fi

if [[ "$chosen"  ==  "L" ]]; then
    python ./floatwm.py float snap --cols 2 --rows 1 --target 1
    exit
elif [[ "$chosen"  ==  "R" ]]; then
    python ./floatwm.py float snap --cols 2 --rows 1 --target 2
    exit
elif [[ "$chosen"  ==  "T" ]]; then
    python ./floatwm.py float snap --cols 1 --rows 2 --target 1
    exit
elif [[ "$chosen"  ==  "B" ]]; then
    python ./floatwm.py float snap --cols 1 --rows 2 --target 2
    exit
elif [[ "$chosen"  ==  "C" ]]; then
    python ./floatwm.py float reset
    exit
elif [[ "$chosen"  ==  "X" ]]; then
    custom="$($rofi_command -dmenu -selected-row 0)"
    IFS=' ' read -ra r_c_t <<< "$custom"
    if [[ "${#r_c_t[@]}" != "3" ]]; then
        echo "Incorrect Argument Length (Need Row, Col, Target)"
        exit
    fi
    echo "target: ${r_c_t[2]}"
    python ./floatwm.py \
      float snap  \
      --cols ${r_c_t[1]} --rows ${r_c_t[1]}  \
      --target ${r_c_t[2]}
    exit
fi

python ./floatwm.py float snap --cols 2 --rows 2 --target $chosen
