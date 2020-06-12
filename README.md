# i3-grid

i3, our beloved window manager, has placed an emphasis on tiling and tabbed layouts. i3 lets the user handle the floating components themselves, while providing many tools to do so (scratch pads, marks, etc). Finding the management of floating windows lackluster, I decide to write a sub-manager for tackling floating windows.

<img align="right" src="https://i.imgur.com/UohcW2v.png">

The lack of standard tools has resulted in personalized scripts [scattered](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) throughout GitHub which are inefficient and static to the user. This module aims to allow for fast and dynamic floating window management with minimal input. i3-grid is also monitor agnostic and has a clean rofi interface with highly configurable commands.

Current planned updates include templates (automating startup and grid management), temporary scratch pads (similar to minimizing windows), and potentially a daemon to auto snap floating windows to quadrants (similar to tiling mode).

## Demo:

<img src="https://i.imgur.com/0QVD4sd.gif">

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Quick start

### Requirements

- i3
- i3-py
- Python3

### Installation

Install via Python:

    pip3 install --user i3-grid

Install via GitHub:

    git clone https://github.com/justahuman1/i3-grid.git

    cd i3-grid/i3-grid/

    *This requires changing the `src_file` variable in the manager.sh rofi script.

Install via AUR:

    yay i3-grid

### Configuration

1.  Automated setup ([Script](https://raw.githubusercontent.com/justahuman1/i3-grid/master/build/install.sh)):

        bash <( curl -s https://raw.githubusercontent.com/justahuman1/i3-grid/master/build/install.sh )

**OR**

1.  Manual setup:

    1.  Create a dotfile (`.i3gridrc`). Possible locations are:

            # More specific locations are searched first and will override the previous

            ~/.i3gridrc
            ~/.config/i3gridrc
            ~/.config/i3grid/i3gridrc

    1.  Downloading the Rofi UI (_Optional_)

            # Place these files in any location you plan to run the application from.
            # The default location is ~/.config/i3grid/{manager.sh, matrix.rasi}

            curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/manager.sh > manager.sh
            curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/matrix.rasi > matrix.rasi

2.  Shortcuts:

Assign i3 shortcuts for dmenu (_Optional_)

    # This is the default shortcut, but feel free to change to a more preferable key.
    bindsym mod+o ~/.config/i3grid/manager.sh

    # Dedicated shortcuts for frequently used commands (less keystrokes)
    bindsym mod+c python3 -m i3grid center

ZSH Alias (_Optional_)

    alias i3grid="python3 -m i3grid"

### Basic Usage:

Help menu

    python3 -m i3grid -h
        *Can be added to path to simply call `i3grid` on the cli

Center window

    python3 -m i3grid center

Top right corner

    python3 -m i3grid snap --target 2  # Using default rc

See the following for more detailed examples:

[CLI Examples](https://github.com/justahuman1/i3-grid/blob/master/rofi/manager.sh),
[Library Examples](https://github.com/justahuman1/i3-grid/blob/master/lib_example.py)

## Features

- Reshape and pin floating windows to any precise locations on screen
- Intuitive rofi \*frontend (Fully customizable with Vim keybindings)
- Full-featured CLI and Library; includes event listeners (via streaming socket data)
- On the fly workspaces (apply actions to multiple windows)
- Deep customization with powerful out of the box features
- Supports Multiple Monitor Setups

\*<sub>Rofi not necessary for functionality (separate dmenu layer)</sub>

### Rofi Vim Bindings

Default bindings using the arrow keys and enter keys are available. Vim keys are supported improve the user speed of using the UI.

    - h: row left
    - j: row down
    - k: row up
    - l: row right
    - m: enter
    - n: multi-select
    - b: backspace
    - c: clear text
    - e: escape

> NOTE: The keybindings interfere with the search. To search for 'h', use shift to bypass and search with the letter 'H'.
> All keybindings can be changed in the `matrix.rasi` file under the \*configuration block (`kb-*`)

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

- Hide all scratch pads with one action (and filter floating windows)
- Transform all windows in the current screen with a single command (`all` flag)
- Dynamic monitor sizing (xrandr parsing)

## Known Bugs

- Search indexing is suboptimal for double digits (rofi limitations)
- Rofi UI does not resize dynamically for large col and row digits

## Crushed Bugs

- ~~Multi-select resizing does not stretch horizontally~~
- ~~Left & Right offsets are inaccurate (Applies to both sides)~~
- ~~Multiple Monitors are not supported~~
