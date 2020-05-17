#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import subprocess
import sys
from collections import namedtuple
from typing import Dict, List

import i3
import yaml
from i3 import Socket
try:
    from doc import Documentation
except ModuleNotFoundError:
    pass

""" i3_float_wm is a script to manage floating windows for the
i3 tiling window manager. The code is split into several classes, which isolate
the logic respective to its name. The process flow is as follows:

    1) FloatManager: Manages the user input parsing and function dispatches.
    2) Movements: Contains the functions that are directly called by the user to invoke window actions.
    3) MonitorCalculator: Manages the xrandr display settings to make display agnostic window decisions.
    4) FloatUtils: The meta functions of the manager that directly assist the movements and calculator.
    5) Utils: Additional utilities to abstract debugging, RPC calls, etc.
-------------
License:
    Copyright (C) 2020 justahuman1

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# Formatted with Black: https://github.com/psf/black

# Custom Types
# The x and y coordinates of any X11 object
Location = namedtuple("Location", "width height")
# A vector of location objects
Tensor = List[Location]
# Represents the display monitor to their respective index
DisplayMap = Dict[int, Location]

# Globals used for config
AUTO_FLOAT_CONVERT = False
AUTO_RESIZE = False
SNAP_LOCATION = 0
CUSTOM_PERCENTAGE = 50
RC_FILE_NAME = "floatrc"
DEFAUlT_GRID = {"rows": 2, "cols": 2}
# Follows CSS format
# [Top, Right, Bottom, Left]
TILE_OFFSET = [0, 0, 0, 0]
DISPLAY_MONITORS = {
    "eDP1",
    "HDMI1",
    "VGA",
}

# TODO: handle multiple monitor (behind summation) offset


class Utils:
    """External utilities for
    external I/O commands and
    user configurations."""

    def __init__(self,) -> None:
        super().__init__()

    @staticmethod
    def dipatch_bash_command(command_str: str) -> str:
        if not command_str or command_str.strip() == "":
            raise ValueError("null command")

        out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        return out.stdout

    @staticmethod
    def dispatch_i3msg_com(command: str, data: Location = Location(1189, 652)) -> list:
        # Immutable location tuple accounts for mutation error
        if not isinstance(data, (list, tuple)) and len(data) == 2:
            raise ValueError("Incorrect data type/length for i3 command")

        dispatcher = {
            # Dictionary of commands to execute with i3 comx
            "resize": lambda *d: i3.resize("set", d[0], d[1]),
            "move": lambda *d: i3.move("window", "position", d[0], d[1]),
            "float": lambda *d: i3.floating("enable"),
            "reset": lambda *d: (
                i3.resize("set", "75ppt", "75ppt")
                and i3.move("window", " position", "center")
            ),
            "custom": (
                lambda *d: i3.resize("set", d[0], d[0])
                and i3.move("window", "position", "center")
            ),
        }
        if isinstance(data, str):
            dispatcher[command](data)
        elif isinstance(data, Location):
            w = str(data.width) if data.width > 0 else "0"
            h = str(data.height) if data.height > 0 else "0"
            dispatcher[command](w, h)

    @staticmethod
    def get_cmd_args(elem: int = None) -> (Location, int):
        try:
            if not elem:
                return [int(i) for i in sys.argv[1:]] or [4, 4]

            if elem > len(sys.argv[1:]):
                return None
            elif len(sys.argv[1:]) < 2:
                return [4, 4][elem]
            return int(sys.argv[elem])

        except ValueError:
            return [4, 4]

    @staticmethod
    def read_config() -> None:
        global DISPLAY_MONITORS, RC_FILE_NAME
        global AUTO_FLOAT_CONVERT, DEFAUlT_GRID
        global SNAP_LOCATION, AUTO_RESIZE
        global TILE_OFFSET

        default_locs = [
            f"~/.config/i3float/{RC_FILE_NAME}" f"~/.config/{RC_FILE_NAME}",
            f"~/.{RC_FILE_NAME}",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), f".{RC_FILE_NAME}"
            ),
        ]
        target_loc = None
        for loc in default_locs:
            if os.path.isfile(loc):
                target_loc = loc
                break

        if not target_loc:
            raise ValueError(
                "No dotfile config found. "
                "Add to ~/.floatrc or ~/.config/floatrc "
                "or ~/.config/i3float/floatrc"
            )

        with open(target_loc, "r") as f:
            config = yaml.safe_load(f)
        if not config or "Settings" not in config:
            raise ValueError(
                "Incorrect floatrc file sytax. Please follow yaml guidelines and example."
            )

        # This turned into a really bad design. I need
        # to simply keep a global dictionary so we can dynamically
        # parse the yaml file. I will do this after mvp.
        # But this way is much more seralized for OOP (scalability).
        snap_yml_key = "SnapLocation"
        grid_yml_syn = ["Rows", "Columns"]
        grid_yml_key = "DefaultGrid"
        offs_yml_key = "GridOffset"
        monitors_yml_key = "DisplayMonitors"
        auto_yml_key = "AutoConvertToFloat"
        resize_yml_key = "AutoResize"
        settings = config["Settings"]

        if resize_yml_key in settings:
            AUTO_RESIZE = settings[resize_yml_key]
        if auto_yml_key in settings:
            AUTO_FLOAT_CONVERT = True if settings[auto_yml_key] else False
        if monitors_yml_key in settings:
            DISPLAY_MONITORS = tuple(m for m in settings[monitors_yml_key])
        if offs_yml_key in settings:
            TILE_OFFSET = settings[offs_yml_key]
        if grid_yml_key in settings:
            DEFAUlT_GRID = {
                "rows": settings[grid_yml_key][grid_yml_syn[0]],
                "cols": settings[grid_yml_key][grid_yml_syn[1]],
            }

        if snap_yml_key in settings:
            if isinstance(settings[snap_yml_key], int):
                SNAP_LOCATION = settings[snap_yml_key]
            else:
                raise ValueError("Unexpected Snap location data type (expected int)")

    @staticmethod
    def on_the_fly_override(**kwargs) -> None:
        global SNAP_LOCATION, DEFAUlT_GRID
        global CUSTOM_PERCENTAGE, AUTO_RESIZE
        global AUTO_FLOAT_CONVERT
        r = "rows"
        c = "cols"
        t = "target"
        p = "perc"
        nr = "noresize"
        nf = "nofloat"
        verify = lambda key: key in kwargs and kwargs[key]

        if verify(r):
            DEFAUlT_GRID[r] = kwargs[r]
        if verify(c):
            DEFAUlT_GRID[c] = kwargs[c]
        if verify(t):
            SNAP_LOCATION = kwargs[t]
        if verify(p):
            CUSTOM_PERCENTAGE = kwargs[p]
        if verify(nr):
            AUTO_RESIZE = not kwargs[nr]
        if verify(nf):
            AUTO_FLOAT_CONVERT = not kwargs[nf]


class FloatUtils:
    """Utilities directly utilized
    by the float manager for i3 workspace
    metadata."""

    def __init__(self) -> None:
        self.area_matrix, self.current_display = self._calc_metadata()
        assert len(self.current_display) > 0, "Incorrect Display Input"

    def assign_focus_node(self) -> None:
        tree = i3.get_tree()
        # for node in tree:
        wkspc = [
            node
            for node in tree["nodes"]
            if node["name"] == self.current_display["output"]
        ]
        assert len(wkspc) > 0, "window could not be found"
        self.iter = 0
        for w in wkspc:
            self.find_focused_window(w)

    def find_focused_window(self, node: dict) -> None:
        """Sets the focused_node attribute"""
        # DFS to find the current window
        self.iter += 1
        if not isinstance(node, dict):
            return
        if node["focused"]:
            self.focused_node = node
            return

        if (len(node["nodes"]) != 0) or (len(node["floating_nodes"]) != 0):
            target_nodes = node["nodes"] + node["floating_nodes"]
            for root in target_nodes:
                self.find_focused_window(root)
        else:
            return

    def _calc_metadata(self) -> (DisplayMap, dict):
        self.displays = i3.get_outputs()
        print('All displays')
        print(self.displays)

        # Widths * Lengths (seperated to retain composition for children)
        total_size = {}
        monitor_cnt = 0
        for display in self.displays:
            if display["name"] not in DISPLAY_MONITORS:
                continue
            display_screen_location = Location(
                width=display["rect"]["width"], height=display["rect"]["height"]
            )
            total_size[monitor_cnt] = display_screen_location
            monitor_cnt += 1

        active = [i for i in i3.get_workspaces() if i["focused"]][0]
        return total_size, active

    def get_wk_number(self) -> int:
        c_monitor = 0
        for display in self.displays:
            print(display)
            if display["name"] in DISPLAY_MONITORS:
                if self.match(display):
                    break
                c_monitor += 1
        return c_monitor

    def match(self, display: dict) -> bool:
        validations = [["name", "output"], ["current_workspace", "name"], "rect"]
        for val in validations:
            if val == "rect":
                if display[val]["width"] != self.current_display[val]["width"]:
                    return False
            elif display[val[0]] != self.current_display[val[1]]:
                return False
        return True

    def get_i3_socket(self) -> Socket:
        return i3.Socket()


class MonitorCalculator(FloatUtils):
    def __init__(self,) -> None:
        super().__init__()
        self.cache_grid = None
        self.cache_resz = None

    def calc_monitor_offset(
        self, mode: str, point: Location, loc: int = None
    ) -> Location:
        if mode == "resize" and self.cache_resz:
            return self.cache_resz

        rows = DEFAUlT_GRID["rows"]
        cols = DEFAUlT_GRID["cols"]
        assert SNAP_LOCATION <= (rows * cols), "Incorrect Target in grid"
        # Check if target around border
        # if so, apply offset/(num rows or cols) (if resize)
        # if snap and border, apply full offset > + | -
        # if border:
        mode_defs = {
            "snap": lambda *d: TILE_OFFSET[d[0]],
            "resize": lambda *xy: int(
                (TILE_OFFSET[xy[0]] + TILE_OFFSET[xy[1]]) / (xy[2] or 1)
            ),
        }
        # [x, y] axis of grid index
        chosen_axis = self.find_grid_axis()
        cur_axis = self.find_grid_axis(loc=loc)
        t_h = point.height
        t_w = point.width
        if mode == "resize":
            r_l = mode_defs[mode](1, 3, cols)
            t_b = mode_defs[mode](0, 2, rows)

            self.cache_resz = Location(
                t_w - r_l, t_h - t_b,
            )
            return self.cache_resz
        elif mode == "snap":
            per_offset = [int(i) for i in TILE_OFFSET]
            return Location(
                width=per_offset[1],
                height=per_offset[0],
            )

        return Location(t_w, t_h)

    def get_offset(self, center: bool = True) -> Location:
        # No globals required (read only)
        # 1) Calculate monitor center
        # 2) Calculate window offset
        # 3) Monitor center - offset = true center
        # 3 if) tensors are intersecting
        display = self.area_matrix[self.workspace_num]
        window = self.get_target(self.focused_node)
        if center or SNAP_LOCATION == 0:
            # Abs center (2, 2)
            display_offset, target_offset = self.get_matrix_center(
                2, 2, display, window
            )
        else:
            display_offset = target_offset = Location(0, 0)
            target = SNAP_LOCATION
            # y, x adjusted for accessing matrix
            y, x = self.find_grid_axis()
            # 1 is the location (0 is the index)
            return self.float_grid[y][x][1]

        # Heigh is half of the respective monitor
        # The tensors are parallel hence, no summation.
        # local *centers (not abs)
        center_x = display_offset.width - target_offset.width
        center_y = display_offset.height - target_offset.height
        return Location(center_x, center_y)

    def find_grid_axis(self, loc: int = None):
        # row, col
        loc = loc or SNAP_LOCATION
        return divmod(loc - 1, DEFAUlT_GRID["cols"])

    def calculate_grid(self, rows: int, cols: int, display: Location) -> Tensor:
        if self.cache_grid:
            return self.cache_grid
        main_loc = Location(int(display.width / cols), int(display.height / rows))
        # Account for window size offset (grid quadrant size - offset/(rows | cols))
        self.per_quadrant_dim = self.calc_monitor_offset("resize", main_loc)
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        i = 1
        rolling_dimension = Location(0, 0)
        row_match = roll_width = roll_height = 0
        carry_flag = True
        for row in range(len(grid)):
            row_tracker = row
            for col in range(len(grid[row])):
                if row != 0 or col != 0:  # Top row and left col
                    roll_width = rolling_dimension.width + self.per_quadrant_dim.width
                if row_match != row_tracker:
                    roll_height = (
                        rolling_dimension.height + self.per_quadrant_dim.height
                    )
                    row_match = row_tracker
                    roll_width = 0
                # Roll from previous grid number
                rolling_dimension = Location(roll_width, roll_height)
                if carry_flag:
                    overlay_top = self.calc_monitor_offset(
                        "snap", rolling_dimension, loc=i
                    )
                    adjusted = Location(  # Adjust for offset
                        abs(roll_width - overlay_top.width),
                        abs(roll_height + overlay_top.height),
                    )
                else:
                    adjusted = Location(roll_width, roll_height)
                grid[row][col] = (i, adjusted)
                i += 1
        self.cache_grid = grid
        return grid

    def get_matrix_center(self, rows, cols, *windows: Location) -> Location:
        return [
            Location(int(window.width / rows), int(window.height / cols))
            for window in windows
        ]


class Movements(MonitorCalculator):
    def __init__(self,) -> None:
        super().__init__()
        # Contains all the cache keys for movements
        self.cache_monitor_grid = "monitor_grid"

    def move_to_center(self, **kwargs) -> None:
        """Moves the focused window to
        the absolute window center (corresponds to
        target=0)"""
        # True center (accounting for multiple displays)
        # The height vector is difficult to calculate due to XRandr
        # offsets (that can extend in any direction).
        true_center = self.get_offset()
        # Dispatch final command
        Utils.dispatch_i3msg_com(command="move", data=true_center)

    def make_resize(self, **kwargs) -> None:
        target_size = self.per_quadrant_dim
        Utils.dispatch_i3msg_com("resize", data=target_size)

    def custom_resize(self, **kwargs) -> None:
        Utils.dispatch_i3msg_com("custom", data=f"{CUSTOM_PERCENTAGE}ppt")

    def get_target(self, node) -> None:
        return Location(width=node["rect"]["width"], height=node["rect"]["height"])

    def snap_to_grid(self, **kwargs) -> None:
        """Moves the focused window to
        the target (default: 0) position in
        current grid (default: 2*2)"""
        target_pos = self.get_target(self.focused_node)
        true_center = self.get_offset(center=False,)

        Utils.dispatch_i3msg_com("move", true_center)

    def reset_win(self, **kwargs) -> None:
        """Moves to center and applies default tile
        to float properties (center, 75ppt)"""
        Utils.dispatch_i3msg_com(command="reset")

    def make_float(self, **kwargs) -> None:
        """Moves the current window into float mode
        if it is not float. If float, do nothing. Does not
        resize (feel free to combine) but i3 does so by default
        sometimes (based on config and instance rules)."""
        Utils.dispatch_i3msg_com(command="float")


class FloatManager(Movements):
    def __init__(self, **kwargs) -> None:
        """Manager > Movement > Calculator > Utility > Dispatch event"""
        super().__init__()
        # 1) Read config and merge globals
        Utils.read_config()
        # 2) Override to on the fly settings
        Utils.on_the_fly_override(**kwargs)

        # Run initalizing commands
        # partitioned for multiple commands
        self.post_commands()
        if AUTO_FLOAT_CONVERT:
            self.make_float()
            # Resync to state
            self.post_commands()
        if AUTO_RESIZE:
            self.make_resize()
            # Resync to state
            self.post_commands()

        executors = [
            self.move_to_center,
            self.make_float,
            self.make_resize,
            self.snap_to_grid,
            self.custom_resize,
            self.reset_win,
        ]
        self.com_map = {c: e for c, e in zip(kwargs["commands"], executors)}

    def run_command(self, cmd: str, **kwargs) -> None:
        if cmd not in self.com_map:
            raise KeyError("No corresponding run command to input:", cmd)
        # Commands that must be refreshed on every action (cheap C socket transfer)
        self.post_commands()
        self.com_map[cmd](**kwargs)

    def post_commands(self) -> None:
        # If not float, make float -> <movement>
        self.workspace_num = self.get_wk_number()
        # exit()
        # Set the focused node
        self.assign_focus_node()
        self.float_grid = self.calculate_grid(
            DEFAUlT_GRID["rows"],
            DEFAUlT_GRID["cols"],
            self.area_matrix[self.workspace_num],
        )


def debugger() -> None:
    """Evaluates user input expression."""
    print("Entering debug mode. Evaluating input:")
    while 1:
        cmd = input(">>> ")
        print(eval(cmd))


if __name__ == "__main__":
    if "debug" in sys.argv:
        debugger()
        exit(0)

    start = datetime.datetime.now()
    try:
        doc = Documentation()
    except NameError:
        print("Missing Documentation (doc.py).")
        exit(1)

    comx = list(doc.actions)
    parser = doc.build_parser(choices=comx)
    args = parser.parse_args()
    # Manager can simply be an unpacker
    # to args, rather than manual
    # seralizing into kwargs.
    manager = FloatManager(commands=comx, **args.__dict__,)
    for action in args.actions:
        manager.run_command(cmd=action)

    end = datetime.datetime.now()
    print("Total Time: ", end - start)
    exit(0)
