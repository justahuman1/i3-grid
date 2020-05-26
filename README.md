# i3-grid

i3, our beloved window manager, has placed an emphasis on tiling and tabbed layouts. i3 lets the user handle the floating components themselves, while providing many tools to do so (scratch pads, marks, etc). Finding the management of floating windows lackluster, I decide to write a sub-manager for tackling floating windows to solidify this aspect of i3.

<img style="float: right" src="https://i.imgur.com/UohcW2v.png">

The lack of standard tools has resulted in personalized scripts [scattered](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) throughout GitHub which are inefficient and static to the user. This module aims to allow for fast and dynamic floating window management with minimal input. Oh yeah, it's also monitor agnostic and has a clean rofi interface with highly configurable commands.

Current planned updates include templates (automating startup and grid management), temporary scratch pads (similar to minimizing windows), and potentially a daemon to auto snap floating windows to quadrants (similar to tiling mode).

## Demo:

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Quick start

### Requirements

- i3
- i3-py
- Python

### Installation

Install via Python:

    pip3 install --user i3-grid

    python3 -m i3grid -h
        *Can be added to path to simply call `i3-grid` on the cli

Install via GitHub:

    git clone https://github.com/justahuman1/i3-grid.git

    cd i3-grid/ && python3 -m i3grid -h

Install via AUR:

    yay python-i3-grid

    i3grid -h

### Configuration

1. Create a dotfile (`.i3gridrc`). Possible locations are:

   ~/.i3gridrc
   ~/.config/i3gridrc
   ~/.config/i3grid/i3gridrc

   # More specific locations are searched first and will override the previous

Downloading the Rofi UI

    curl xyz

## Features

- Reshape and pin floating windows to any precise locations on screen
- Intuitive rofi \*frontend (Fully customizable with Vim keybindings)
- Full-featured CLI and Library; includes event listeners (via streaming socket data)
- On the fly workspaces (apply actions to multiple windows)
- Deep customization with powerful out of the box features
- Supports Multiple Monitor Setups

\*<sub>Rofi not necessary for functionality (separate dmenu layer)</sub>

## Todos

PR's very welcome. Order of importance will be according to issues and PR count.

- Templating feature for quick floating env startup (Top Current Priority)
- Let user choose window by using xprop and filter window to apply action
- Deep scratch pad integration (Drop-down list and temporary pads)
- Add cache registers for assigning keys on the fly
- Dynamic Rofi menu (width, height) to personal rc config settings
- Restore all scratch pads with one action
- Additional Options:
  - Send all floating windows to a temporary scratch pad (accessible via rofi)
  - Fill the remaining of the floating screen with new window (Recursive stack)
  - Add a history options to Rofi Menu (Previously ran commands)
  - Advanced Rofi menu (allowing complex command generation on the fly)
  - Daemon to listen for screen changes and make background window transformations
    - Probably will need to be written in C/Go (performance concerns).

## Recently Added

- Hide all scratch pads with one action
- Transform all windows in the current screen with a single command (`all` flag)!
- Dynamic monitor sizing (xrandr parsing)

## Known Bugs

- Search indexing is suboptimal for double digits (rofi limitations)

## Crushed Bugs

- ~~Multi-select offset resizing (Does not respect all offsets)~~
- ~~Left & Right offsets are inaccurate (Applies to both sides)~~
- ~~Multiple Monitors are not supported~~
