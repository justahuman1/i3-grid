# i3 Floating WM

i3, our beloved window manager, is just that. A tiling window manager. It lets the user handle the floating components themselves, while providing many tools to do so (scratchpads, marks, etc). The lack of standard tools has resulted in personalized scripts scattered throughout GitHub without a standardized manner to combat floating windows. Not for long! This script aims to allow for fast floating window management with minimal input. Oh yeah, it's also monitor agnostic!

## Demo:

Why does this exist?<sup>[1](https://github.com/i3/i3/issues/1949#issuecomment-142231260)</sup> <sup>[2](https://www.reddit.com/r/i3wm/comments/97hc7u/how_to_move_window_relative_to_display/e4955ff/)</sup> <sup>[3](https://gist.github.com/bhepple/5c43e83e945a42297ba6433ee8ba88ce) </sup>

## Installation

## Features

- Rofi \*frontend (Fully customizable)
- Python CLI and Library (includes event listeners for additional scripting)
- Reshape and pin floating windows to any precise locations on screen
- On the fly workspaces
- Deep customization with powerful out of the box features

\*<sub>Rofi not necessary for functionality (seperate dmenu layer)</sub>

## Todos

PR's very welcome :). Order of importance will be according to issues and PR count.

- Remember Previous option and automatically follow "on the fly grid" (cache)
- Dynamic Rofi menu to rc config file (Adjust height and width)
- Support Multiple Screens (Important!)
- Deep scratchpad integration
- Templating feature for quick floating env startup
- Additional Options:
  - Send all floating windows to a temporary scratchpad (accessible via rofi)
  - Fill up the rest of the screen with new window (Recursive stack)
  - Add a history options to Rofi Menu
  - Advanced Rofi menu (allowing complex command generation on the fly)

## Known Bugs

- Multi-select offset resizing (Does not respect all offsets)
