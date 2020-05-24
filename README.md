# i3-grid

i3, our beloved window manager, is just that. A tiling window manager. It lets the user handle the floating components themselves, while providing many tools to do so (scratch pads, marks, etc). The lack of standard tools has resulted in personalized scripts scattered throughout GitHub without a standardized manner to combat floating windows. Not for long! This script aims to allow for fast floating window management with minimal input. Oh yeah, it's also monitor agnostic!

## Demo:

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Quickstart

Install via Python:

    pip install i3-grid

    python -m i3grid -h

Install via GitHub:

    git clone https://github.com/justahuman1/i3-grid.git

    cd i3-grid/ && python -m i3grid -h

Install via AUR:

    yay install i3-grid

    i3grid -h

## Features

- Reshape and pin floating windows to any precise locations on screen
- Intuitive rofi \*frontend (Fully customizable)
- Full-featured CLI and Library; includes event listeners (via streaming socket data)
- On the fly workspaces (apply actions to multiple windows)
- Deep customization with powerful out of the box features
- Supports Multiple Monitor Setups

\*<sub>Rofi not necessary for functionality (separate dmenu layer)</sub>

## Todos

PR's very welcome. Order of importance will be according to issues and PR count.

- Templating feature for quick floating env startup (Top Current Priority)
- Restore all scratch pads with one action
- Deep scratch pad integration (Drop-down list and temporary pads)
- Remember Previous option and sequentially follow the grid trend (cache)
- Dynamic Rofi menu (width, height) to personal rc config settings (with Vim keys)
- Additional Options:
  - Send all floating windows to a temporary scratch pad (accessible via rofi)
  - Fill the remaining of the floating screen with new window (Recursive stack)
  - Add a history options to Rofi Menu (Previously ran commands)
  - Advanced Rofi menu (allowing complex command generation on the fly)
  - Daemon to listen for screen changes and make background window transformations
    - Probably will need to be written in C (performance concerns).

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
