# i3-grid

i3, our beloved window manager, has placed an emphasis on tiling and tabbed layouts. i3 lets the user handle the floating components themselves, while providing many tools to do so (scratch pads, marks, etc). Finding the management of floating windows lackluster, I decide to write a sub-manager for tackling floating windows.

<img align="right" src="https://i.imgur.com/UohcW2v.png">

The lack of standard tools has resulted in personalized scripts [scattered](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) throughout GitHub which are inefficient and static to the user. This module aims to allow for fast and dynamic floating window management with minimal input. i3-grid is also monitor agnostic and has a clean rofi interface with highly configurable commands.

Current planned updates include templates (automating startup and grid management), temporary scratch pads (similar to minimizing windows), and potentially a daemon to auto snap floating windows to quadrants (similar to tiling mode). _Please keep in mind that i3-grid is still in beta. Issues are bound to happen_.

**September 2020: ~~Rofi has been updated to v1.6.0 and presents some breaking UI changes. A fix has been started. (Functionality is still stable).~~ UI is patched & stable (Updated matrix.rasi).**

```
 pip install --upgrade i3-grid
 curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/.i3gridrc > ~/.config/i3grid/i3gridrc
```

## Demo:

<p align="center">
  <img src="https://i.imgur.com/0QVD4sd.gif"/>
</p>
<p align="center">
  <img src="https://i.imgur.com/y3jEaBr.png"/>
</p>

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Quick start

### Requirements

- i3
- xrandr
- Python3

### Installation

Install via Python:

    pip3 install --user i3-grid

Install via AUR:

    yay i3-grid

Install via GitHub:

    git clone https://github.com/justahuman1/i3-grid.git --branch 0.2.3b3

    rofi:
        # This requires changing the `grid_src` variable in the manager.sh script
        cd i3-grid/rofi && ./manager.sh

    cli:
        cd i3-grid/i3-grid && python3 -m i3grid -h

### Configuration

1.  Automated setup ([Script](https://raw.githubusercontent.com/justahuman1/i3-grid/master/build/install.sh)):

        bash <( curl -s https://raw.githubusercontent.com/justahuman1/i3-grid/master/build/install.sh )

    <details>
    <summary>Manual setup (Not Recommended)</summary>
    <br>

            1.  Create a dotfile (`.i3gridrc`).

                    mkdir ~/.config/i3grid && cd ~/.config/i3grid
                    curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/.i3gridrc > i3gridrc

                    # More specific locations are searched first and will override the previous. Possible locations:
                        ~/.i3gridrc
                        ~/.config/i3gridrc
                        ~/.config/i3grid/i3gridrc

            2.  Downloading the Rofi UI (*Optional | Minimum rofi version: 1.5.2)

                    # Place these files in any location you plan to run the application from.
                    # The default location is ~/.config/i3grid/{manager.sh, matrix.rasi, i3gridrc}

                    curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/manager.sh > manager.sh
                    curl https://raw.githubusercontent.com/justahuman1/i3-grid/master/rofi/matrix.rasi > matrix.rasi
                    chmod +x manager.sh

    </details>

2.  Shortcuts:

Assign i3 shortcuts for dmenu (_Optional_)

    # This is the default shortcut, but feel free to change to a more preferable key.
    bindsym mod+o exec /bin/bash ~/.config/i3grid/manager.sh

    # Dedicated shortcuts for frequently used commands (less keystrokes)
    bindsym $mod+c exec "python3 -m i3grid reset"

ZSH Alias (_Optional_)

    alias i3grid="python3 -m i3grid"

### Basic Usage:

Help menu

    python3 -m i3grid -h

Center window

    python3 -m i3grid center

Bottom right corner (_Change offsets in the rc file if necessary_)

    python3 -m i3grid snap --target 4 --rows 2 --cols 2

Rofi UI

    ~/.config/i3grid/manager.sh

See the following for more detailed examples:

[CLI Examples](https://github.com/justahuman1/i3-grid/blob/master/rofi/manager.sh),
[Library Examples](https://github.com/justahuman1/i3-grid/blob/master/lib_example.py)

### i3 Modes:

Modes prevent having to sacrifice multiple key shortcuts. This maps the left side of the
keyboard to quadrants on your monitor (reflective of the key in position of the board).
Once you enter this mode, toggle different window shapes and exit mode to default actions.

```
# Grid floating windows
mode "i3grid" {
    bindsym q exec "python3 -m i3grid snap --cols 2 --rows 2 --target 1"
    bindsym e exec "python3 -m i3grid snap --cols 2 --rows 2 --target 2"
    bindsym z exec "python3 -m i3grid snap --cols 2 --rows 2 --target 3"
    bindsym c exec "python3 -m i3grid snap --cols 2 --rows 2 --target 4"

    bindsym w exec "python3 -m i3grid snap --cols 1 --rows 2 --target 1"
    bindsym x exec "python3 -m i3grid snap --cols 1 --rows 2 --target 2"

    bindsym a exec "python3 -m i3grid snap --cols 2 --rows 1 --target 1"
    bindsym d exec "python3 -m i3grid snap --cols 2 --rows 1 --target 2"
    bindsym s exec "python3 -m i3grid reset"
    bindsym f exec "python3 -m i3grid csize --perc 100"

    bindsym g exec "python3 -m i3grid csize --perc 33"
    bindsym h exec "python3 -m i3grid csize --perc 50"
    bindsym j exec "python3 -m i3grid csize --perc 66"
    bindsym k exec "python3 -m i3grid csize --perc 85"
    bindsym l exec "python3 -m i3grid csize --perc 92"
    bindsym p exec "python3 -m i3grid snap --cols 3 --rows 3 --target 3"
    bindsym o exec "python3 -m i3grid snap --cols 3 --rows 3 --target 2"
    bindsym i exec "python3 -m i3grid snap --cols 3 --rows 3 --target 1"

    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym m mode "default"
    bindsym n mode "default"
}
bindsym $mod+shift+o mode "i3grid"
```

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
- Percentage commands do not work with older versions of i3. Possible workarounds in consideration.

## Crushed Bugs

- ~~Multi-select resizing does not stretch horizontally~~
- ~~Left & Right offsets are inaccurate (Applies to both sides)~~
- ~~Multiple Monitors are not supported~~
