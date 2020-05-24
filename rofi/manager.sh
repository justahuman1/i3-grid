#!/usr/bin/env bash

#  GitHub: justahuman1
#  URL: https://github.com/justahuman1
#  License: GPL-3.0
#  Copyright (C) 2020 Sai Valla
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

# ---- Rofi Frontend ----
# FIXME: Currently, the grid resizing is static. If you change it to a different
# number, you *may need to change the height and width correspondingly in the rasi file.
# Control rofi theming here (Deep configuration available in the rasi file)
# Too many env vars will slow down the load time, hence limitation.

## Theming
export COLS=4   # Corresponds to grid layout of the screen (X,Y)
export LINES=4
export BG="#000000"                     # Panel Background
export TXT="#bdc3c3"                    # Text color
export GRID_FONT="Iosevka 13"           # Font (Include size)
export ACTIVE="rgba(9, 145, 224, 0.4)"  # Active Cell background
export SBAR="#242222"                   # Search Bar background

## Initalize
join() { local IFS="$1"; shift; echo "$*"; }
# src file absolute path (if i3-grid is not installed)
app_abs_path="/home/sai/Code/FullApps/quadrant/"
rofi_command="rofi -i -theme $app_abs_path/rofi/matrix.rasi -multi-select"
# We use a bash function to dynamically generate the
# grid for different canvases on the fly.
grid=()
_l=$(( $LINES - 1 ))
_carry=$COLS
# Rofi aligned menu
# rows --> Col transformation (This is why search index is wrong).
# We can make this transformation on the Python side but speed tradeoff..
for value in $(seq 1 $COLS); do
  grid+=($value)
  for i in $(seq 1 $_l); do
    mew=$(( $value + $_carry ))
    grid+=($mew)
    i=$(( $i + 1 ))
    _carry=$(( $COLS * $i ))
  done
  _carry=$COLS
done

# Custom Commands
grid+=(
  "C" # Custom Percentage, center window (ofc, you can override otf)
  "D" # Use default rc file rows and col nums to create grid and use input as snap target
  "R" # Reset to i3 default center (75% screen)
  "X" # Custom col, row, target parsing
  "G" # Guake style window
  "A" # Apply snap to all windows in current workspace
  "H" # Hide all workspace floating windows

  ## FIXME: Add command here. Define it's call in the case statement below.
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
# app_abs_path="/home/sai/Code/FullApps/quadrant/i3-grid/i3grid/i3_utils/grid.py"
src_file="$app_abs_path/i3-grid/i3grid/i3_utils/grid.py"

if [[ "$len" -gt "2" ]]; then  # if multi select
  declare -a arr
  arr=( $(echo $chosen | awk '{split($0,a," ")} END {for(n in a){ print a[n] }}') )
  multi_arg=$(join ' ' ${arr[@]})
  python $src_file multi --multis $multi_arg
  exit
elif [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # Catch for non-grid user input
    # Ex: I run raw custom commands that I type into the grid (as outputted by rofi)
    echo "Error: Element Out of grid"
    python $src_file -h
    exit
fi

case "$chosen" in
"A")
  python $src_file snap --all
;;
"C")
  p="$($rofi_command -dmenu -p "% -" -selected-row 0)"
  python $src_file csize --perc=$p
;;
"D")
  target="$($rofi_command -dmenu -p 'Target:' -selected-row 0)"
  python $src_file float resize snap --target $target
;;
"G")
  _h=$(( $COLS * 2 ))
  python $src_file multi --multis 1 $_h --offset 0 130 0 130
;;
"R")
  python $src_file float reset
;;
"H")
  python $src_file hide --noresize --all
;;
"X")
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
;;

# Define custom calls here. Template (Ex: Using custom command 'O'):
# "O")
#   i3-grid <action> <optional-flags>
# ;;

*)
  # Uncomment to see the raw command sent to i3-grid
  # echo "python $src_file float snap --cols $COLS --rows $LINES --target $chosen"
  python $src_file float snap --cols $COLS --rows $LINES --target $chosen
;;
esac
