# i3 Floating WM

i3, our beloved window manager, is just that. A tiling window manager. It lets the user handle the floating components themselves, while providing many tools to do so (scratchpads, marks, etc). The lack of standard tools has resulted in personalized scripts scattered throughout GitHub without a standardized manner to combat floating windows. Not for long! This script aims to allow for fast floating window management with minimal input. Oh yeah, it's also monitor agnostic!

## Demo:

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Installation

## Features

- Reshape and pin floating windows to any precise locations on screen
- Rofi \*frontend (Fully customizable)
- Python CLI and Library (includes event listeners for additional callbacks)
- On the fly workspaces
- Deep customization with powerful out of the box features

\*<sub>Rofi not necessary for functionality (seperate dmenu layer)</sub>

## Todos

PR's very welcome :). Order of importance will be according to issues and PR count.

- Support Multiple Screens (Current Top Priority)
- Templating feature for quick floating env startup
- Remember Previous option and automatically follow trend (cache)
- Dynamic Rofi menu (width, height) to rc config settings
- Deep scratchpad integration (Drop-down list)
- Additional Options:
  - Send all floating windows to a temporary scratchpad (accessible via rofi)
  - Fill the remaining of the floating screen with new window (Recursive stack)
  - Add a history options to Rofi Menu (Previously ran commands)
  - Advanced Rofi menu (allowing complex command generation on the fly)

## Known Bugs

- ~~Multi-select offset resizing (Does not respect all offsets)~~
- ~~Left & Right offsets are wonky (Applies to both sides)~~
