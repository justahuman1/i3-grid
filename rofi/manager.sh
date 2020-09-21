#!/usr/bin/env bash

## ---- Rofi Frontend ----
# Currently, the grid resizing is static. If you change it to a different
# number, you **may need to change the height and width correspondingly in the rasi file.
# Control rofi theming here (Deep configuration available in the rasi file)
# Too many env vars will slow down the load time, hence limitation.

## FIXME: Theming
export COLS=4   # Corresponds to grid layout of the screen (X,Y)
export LINES=4
export BG="#000000"                     # Panel Background
export TXT="#bdc3c3"                    # Text color
export GRID_FONT="Iosevka 13"           # Font (Include size)
export ACTIVE="rgba(9, 145, 224, 0.4)"  # Active Cell background
export SBAR="#242222"                   # Search Bar background
export GWIDTH="200px"                   # Width of rofi widget (240px works well for 5x5 grid)

## FIXME: Path to the src python file/module
grid_src="-m i3grid"
# Uncomment below line if cloned from github
# grid_src="../i3-grid/i3grid"
# The system python interpreter to use
PY_ENV="/usr/bin/python3"

# Initalize
join() { local IFS="$1"; shift; echo "$*"; }
# Absolute path to script (must be in the same folder as matrix.rasi)
app_abs_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
rofi_command="rofi -i -theme $app_abs_path/matrix.rasi -multi-select"
cache_file="$app_abs_path/grid.cache"
# [ -f "$cache_file" ] || touch "$cache_file"  # Make cache file if not exists
RUN_COMMAND="$PY_ENV $grid_src"
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
  "A" # Apply snap to *all windows in current workspace
  "C" # Custom Percentage, center window (ofc, you can override otf)
  "D" # Use default rc file rows and col nums to create grid and use input as snap target
  "F" # Make a window completely full screen (ignores all offsets)
  "G" # Guake style window
  "H" # Hide all workspace floating windows, if scratchpad
  "R" # Reset to i3 default center (75% screen)
  "RR" # ReRun a cached command (drop down option)
  "SF" # Snaps all current *floating windows into a grid
  "X" # Custom col, row, target parsing
  "P"

  ## FIXME: Add command here. Define it's call in the case statement below (line 136).
)
options=""
for i in ${grid[*]}; do
  options="${options}${i}\n"
done
# grid options passed to rofi
chosen="$(echo -e "$options" | $rofi_command -dmenu -p "Grid:" -selected-row 0)"
[ -z "$chosen" ] && exit # Exit if no command is chosen
len=${#chosen}
if [[ "$len" -gt "2" ]]; then  # if multi select
  declare -a arr
  arr=( $(echo $chosen | awk '{split($0,a," ")} END {for(n in a){ print a[n] }}') )
  multi_arg=$(join ' ' ${arr[@]})
  echo "$RUN_COMMAND multi --cols $COLS --rows $LINES --multis $multi_arg" >> $cache_file
elif [[ ! " ${grid[@]} " =~ " ${chosen} " ]]; then
    # Catch non-grid user input
    # Ex: I run raw custom commands that I type into the grid (as outputted by rofi)
    echo "Error: Element Out of grid"
    $RUN_COMMAND -h
    exit
else
  # Grid options
  case "$chosen" in
  "A")
    $RUN_COMMAND snap --all
    exit
  ;;
  "C")
    p="$($rofi_command -dmenu -p "% -" -selected-row 0)"
    [ -z "$p" ] && exit || echo "$RUN_COMMAND csize --perc=$p" >> $cache_file
  ;;
  "D")
    target="$($rofi_command -dmenu -p 'Target:' -selected-row 0)"
    [ -z "$target" ] && exit || echo "$RUN_COMMAND snap --target $target" >> $cache_file
  ;;
  "F")
    $RUN_COMMAND csize --perc 100
    exit
  ;;
  "G")
    $RUN_COMMAND snap --target 1 --rows 2 --cols 1 --offset 0 80 0 80
    exit
  ;;
  "H")
    $RUN_COMMAND hide --noresize --nofloat --all
    exit
  ;;
  "R")
    $RUN_COMMAND reset
    exit
  ;;
  "RR")
    GWIDTH="380px"
    IFS=
    data=$( sort $cache_file | uniq | awk 'NF' | awk '{out=$4; for(i=5;i<=NF;i++){out=out" "$i}; print out}' )
    custom=$( (echo $data) | rofi -i -theme $app_abs_path/matrix.rasi -multi-select -dmenu -p "Cached: ")
    [ -z "$custom" ] && exit || eval "${RUN_COMMAND} ${custom}"  # Run command if not blank else exit
  ;;
  "P")
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
    OUTPUT=$("$DIR/i3classifier.sh")
    $RUN_COMMAND snap --filter "$OUTPUT"
    exit
  ;;
  "SF")
    $RUN_COMMAND snap --floating --rows 3 --cols 2
    exit
  ;;
  "X")
    custom="$($rofi_command -dmenu -p "c r t:" -selected-row 0)"
    IFS=' ' read -ra r_c_t <<< "$custom"
    if [[ "${#r_c_t[@]}" != "3" ]]; then
      echo "Incorrect Argument Length (Requires Row, Col, Target)"
      exit
    fi
    echo "$RUN_COMMAND snap --cols ${r_c_t[0]} --rows ${r_c_t[1]} --target ${r_c_t[2]}" >> $cache_file
  ;;
  ## FIXME Define custom calls here. Template (Ex: Using custom command 'O'):
  # "O")
  #   echo "$RUN_COMMAND <action> <optional-flags>" >> $cache_file
  # ;;
  *)
    # Any number outside the grid can be used as a custom percentage resize
    echo "$RUN_COMMAND csize --perc $chosen" >> $cache_file
    # Uncomment to see the raw command sent to i3-grid (for scripting purposes, etc.)
    # echo "$RUN_COMMAND csize --perc $chosen"
  ;;
  esac
fi
# Run final command (latest)
$(tail -n 1 $cache_file)
