#!/usr/bin/env python
# -*- coding: utf-8 -*-

# License:
#     Copyright (C) 2020 Sai Valla

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import collections
import datetime
import json
import os
import socket
import logging
import subprocess
import sys
import threading
from xrandr.xrandr import XRandR
from collections import namedtuple
from typing import Dict, List

import yaml

import i3
from i3 import Socket

""" i3_float_wm is a script to manage floating windows for the
i3 tiling window manager. The code is split into several classes, which isolate
the logic respective to its name. The process flow is as follows:

    1) FloatManager:      Manages the user input parsing and function dispatches.

    2) Movements:         Contains the functions that are directly
                          called by the user to invoke window actions.

    3) MonitorCalculator: Manages the xrandr display settings
                          to make display agnostic window decisions.

    4) FloatUtils:        The meta functions of the manager that
                          directly assist the movements and calculator.

    5) Utils:             Additional utilities to abstract debugging,
                          RPC calls, etc.
    6) Middleware:        Manages socket connections for API bindings via
                          library or command line.
"""
# Formatted with Black: https://github.com/psf/black

try:
    from doc import Documentation

    collectionsAbc = collections.abc
except ModuleNotFoundError:
    logger.critical("Missing Documentation (doc.py)")
except AttributeError:
    collectionsAbc = collections

__author__ = "Sai Valla"
__version__ = "0.2.1"
__date__ = "2012-05-20"
__license__ = "GNU GPL 3"

# Custom Types
# The x and y coordinates of any X11 object
Location = namedtuple("Location", "width height")
# A vector of location objects
Tensor = List[Location]
# Represents the display monitor to their respective index
DisplayMap = Dict[int, Location]

# Single global for a cleaner shared interface
_CONFIG_GLOBALS = {k: v for k, v in zip(
    [  # snake case keys are non-config keys (unique to implementation only)
     'AutoConvertToFloat', 'AutoResize', 'SnapLocation', 'DefaultGrid',
     'GridOffset', 'DisplayMonitors', 'SocketPort', 'custom_percentage',
     'rc_file_name', 'DefaultResetPercentage'],
    [  # default values for config without any configuration
     True, True, 0, {"Rows": 2, "Columns": 2},
     [0, 0, 0, 0], {"eDP1", "HDMI1", "VGA"}, 65433, 50,
     'floatrc', 75]
)}

# Logger for stdout
logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s |%(lineno)d]: %(message)s')
logger = logging.getLogger(__name__)
# TODO: handle multiple monitor (behind summation) offset
# TODO: range select grid
# TODO: 4*4 rofi
# TODO: float, center, snap all


class Middleware:
    """User middleware for additional event listening.
    Utilizes sockets for instance communication."""

    host = "127.0.0.1"
    port = _CONFIG_GLOBALS['SocketPort']

    def __init__(self,) -> None:
        super().__init__()

    def sync_data(self) -> None:
        global _CONFIG_GLOBALS
        Middleware.port = _CONFIG_GLOBALS['SocketPort']

    def start_server(self, data_mapper: collectionsAbc.Callable):
        """Begins an AF_INET server at the given
        port to listen for floatwm middleware."""
        self.sync_data()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setblocking(1)
            logger.info(f"Binding to: {Middleware.host}/{Middleware.port}")
            s.bind((Middleware.host, Middleware.port))
            s.listen()
            while True:
                # We only have one listener at a time. If we need
                # multiple listeners, we can add threading here.
                conn, addr = s.accept()
                with conn:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        data_mapper(data)
                        # Bidirectional data flow
                        # conn.sendall(data)

    def dispatch_middleware(self, data: str, **kwargs):
        """Client Middleware to send data to server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Our socket is unidirectional for now. We can also allow for
            # user middleware via python/bash if necessary
            s.setblocking(1)
            try:
                s.connect((Middleware.host, Middleware.port))
            except (ConnectionRefusedError, BlockingIOError):
                return
            s.sendall(Middleware.str2bin(data))
            # If we want bidirectional data flow, we can have the client
            # listen to the server for additional events.
            # data = s.recv(1024)

    @staticmethod
    def str2bin(data: str, res_str: bool = False):
        if not isinstance(data, str):
            data = json.dumps(data)
        return (
            data.encode("ascii")
            if not res_str
            else " ".join(format(ord(x), "b") for x in data)
        )


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
        global _CONFIG_GLOBALS
        rc = _CONFIG_GLOBALS['rc_file_name']
        default_locs = [
            f"~/.config/i3float/{rc}",
            f"~/.config/{rc}",
            f"~/.{rc}",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), f".{rc}"
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
                "Incorrect floatrc file sytax. Please"
                " follow yaml guidelines and example."
            )

        settings = config["Settings"]
        for key in settings:
            _CONFIG_GLOBALS[key] = settings[key]
        print(_CONFIG_GLOBALS)
        print('-'*20)

    @staticmethod
    def on_the_fly_override(**kwargs) -> None:
        global _CONFIG_GLOBALS
        cmdline_serializer = [
            ("rows", "Rows"),
            ("cols", "Columns"),
            ("target", "target"),
            ("perc", "DefaultResetPercentage"),
            ("port", "SocketPort"),
            ("offset", "GridOffset"),
            (["noresize", "AutoResize"],),
            (["nofloat", "AutoConvertToFloat"],)]

        def offset_test(o):
            global _CONFIG_GLOBALS
            assert (
                len(o) <= 4
            ), "Incorrect Offset Arguments (Expected 4: t, r, b, l)"

            while len(o) != 4:
                o += [0]
            _CONFIG_GLOBALS['GridOffset'] = [int(i) for i in o]
            _CONFIG_GLOBALS['GridOffset'][1], _CONFIG_GLOBALS['GridOffset'][3] = (
                _CONFIG_GLOBALS['GridOffset'][3], _CONFIG_GLOBALS['GridOffset'][1])

        for cmd_rc in cmdline_serializer:
            res = (kwargs[cmd_rc[0]]
                   if isinstance(cmd_rc[0], str) else kwargs[cmd_rc[0][0]])
            if not res:
                continue
            if len(cmd_rc) == 1:  # boolean configs
                _CONFIG_GLOBALS[cmd_rc[0][1]] = False
            elif cmd_rc[0] == 'offset':
                offset_test(res)
            else:
                _CONFIG_GLOBALS[cmd_rc[1]] = res
        print("On the flied")
        print(_CONFIG_GLOBALS)
        exit()


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
        # print("All displays")
        # print(self.displays)

        # Widths * Lengths (seperated to retain composition for children)
        total_size = {}
        monitor_cnt = 0
        for display in self.displays:
            if display["name"] not in _CONFIG_GLOBALS['DisplayMonitors']:
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
        print(self.displays)
        for display in self.displays:
            # print(display)
            if display["name"] in _CONFIG_GLOBALS['DisplayMonitors']:
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

    def get_xrandr_info(self) -> Location:
        res = Utils.dipatch_bash_command("xrandr --query")
        _err = "xrandr query returned unexpected results"
        assert len(res) >= 50, _err
        if b'current' not in res[:50]:
            raise KeyError(_err)

        data = [i for i in res[:50].split(b',') if b'current' in i]
        assert len(data) == 1, _err

        data = str(data[0].decode('ascii')).split(' ')
        data = [int(i) for i in data if i.isnumeric()]
        assert len(data) == 2, _err

        return Location(data[0], data[1])

    def xrandr_parser(self):
        x = XRandR()
        x.load_from_x()
        return x.configuration


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

        rows = _CONFIG_GLOBALS['DefaultGrid']['Rows']
        cols = _CONFIG_GLOBALS['DefaultGrid']["Columns"]
        assert _CONFIG_GLOBALS['SnapLocation'] <= (rows * cols), "Incorrect Target in grid"
        # Check if target around border
        # if so, apply offset/(num rows or cols) (if resize)
        # if snap and border, apply full offset > + | -
        # if border:
        mode_defs = {
            "snap": lambda *d: _CONFIG_GLOBALS['GridOffset'][d[0]],
            "resize": lambda *xy: int(
                (_CONFIG_GLOBALS['GridOffset'][xy[0]] +
                 _CONFIG_GLOBALS['GridOffset'][xy[1]]) / (xy[2] or 1)),
        }
        # [x, y] axis of grid index
        chosen_axis = self.find_grid_axis()
        cur_axis = self.find_grid_axis(loc=loc)
        t_h = point.height
        t_w = point.width
        if mode == "resize":
            r_l = mode_defs[mode](1, 3, cols)
            t_b = mode_defs[mode](0, 2, rows)

            self.cache_resz = Location(t_w - r_l, t_h - t_b,)
            return self.cache_resz
        elif mode == "snap":
            per_offset = [int(i) for i in _CONFIG_GLOBALS['GridOffset']]
            return Location(width=per_offset[1], height=per_offset[0],)

        return Location(t_w, t_h)

    def get_offset(self, center: bool = True) -> Location:
        # No globals required (read only)
        # 1) Calculate monitor center
        # 2) Calculate window offset
        # 3) Monitor center - offset = true center
        # 3 if) tensors are intersecting
        display = self.area_matrix[self.workspace_num]
        print("Got to display")
        print(_CONFIG_GLOBALS)
        # print(self.xrandr_parser())
        # exit()
        window = self.get_target(self.focused_node)
        if center or _CONFIG_GLOBALS['SnapLocation'] == 0:
            # Abs center (2, 2)
            display_offset, target_offset = self.get_matrix_center(
                2, 2, display, window
            )
        else:
            display_offset = target_offset = Location(0, 0)
            target = _CONFIG_GLOBALS['SnapLocation']
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
        loc = loc or _CONFIG_GLOBALS['SnapLocation']
        return divmod(loc - 1, _CONFIG_GLOBALS['DefaultGrid']["Columns"])

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

    def get_target(self, node: dict) -> None:
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


class FloatManager(Movements, Middleware):
    def __init__(self, **kwargs) -> None:
        """Manager > Movement > Calculator > Utility > Dispatch event"""
        super().__init__()
        # 1) Read config and merge globals
        Utils.read_config()
        # 2) Override to on the fly settings
        Utils.on_the_fly_override(**kwargs)

        # Run initalizing commands
        # partitioned for multiple commands
        self.post_commands()  # Sync to state
        # If not float, make float -> <movement>
        if _CONFIG_GLOBALS['AutoConvertToFloat']:
            self.make_float()
            self.post_commands()  # Resync to state
        if _CONFIG_GLOBALS['AutoResize']:
            self.make_resize()
            self.post_commands()  # Resync to state

        executors = [
            self.move_to_center,
            self.make_float,
            self.make_resize,
            self.snap_to_grid,
            self.custom_resize,
            self.reset_win,
            self.start_server,
        ]
        self.com_map = {c: e for c, e in zip(kwargs["commands"], executors)}

    def run_command(self, cmd: str, **kwargs) -> None:
        """Commands that must be refreshed on
        every action to sync state (C socket data transfer)"""
        if cmd not in self.com_map:
            raise KeyError("No corresponding run command to input:", cmd)
        self.post_commands()  # Resync to state
        threading.Thread(  # Thread middleware to speed up action
            target=self.dispatch_middleware,
            args=({"command": cmd, "modifying_node": self.focused_node},),
        ).start()  # Anonymous thread, since dataflow is unidirectional.
        self.com_map[cmd](**kwargs)

    def post_commands(self) -> None:
        self.workspace_num = self.get_wk_number()
        # Set the focused node
        self.assign_focus_node()
        self.float_grid = self.calculate_grid(
            _CONFIG_GLOBALS['DefaultGrid']["Rows"],
            _CONFIG_GLOBALS['DefaultGrid']["Columns"],
            self.area_matrix[self.workspace_num],
        )


def _debugger() -> None:
    """Evaluates user input expression."""
    logger.info("Entering debug mode. Evaluating input:")
    while 1:
        cmd = input(">>> ")
        logger.info(eval(cmd))


def _sole_commands(args):
    if "listen" in args.actions:
        assert (
            len(args.actions)
        ) == 1, "'Listen' is a sole command. Do not pass additional actions"
        Utils.read_config()
        Utils.on_the_fly_override(port=args.port)
        listener = Middleware()
        try:
            listener.start_server(data_mapper=print)
        except KeyboardInterrupt:
            logger.info("\nClosing Floatwm socket...")
        finally:
            exit(0)


if __name__ == "__main__":
    if "debug" in sys.argv:
        _debugger()
        exit(0)

    start = datetime.datetime.now()
    try:
        doc = Documentation()
    except NameError:
        logger.critical("Missing Documentation (doc.py)")
        exit(1)

    comx = list(doc.actions)
    parser = doc.build_parser(choices=comx)
    args = parser.parse_args()
    # Check for sole commands (Static for now, only 1 value)
    _sole_commands(args)

    # Manager can simply be an unpacker to args,
    # rather than manual seralizing into kwargs.
    manager = FloatManager(commands=comx, **args.__dict__,)
    for action in args.actions:
        manager.run_command(cmd=action)

    end = datetime.datetime.now()
    print("Total Time: ", end - start)
    exit(0)
