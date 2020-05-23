#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import argparse
import collections
import datetime
import json
import logging
import os
import socket
import subprocess
import sys
import threading
from collections import namedtuple
from typing import Dict, List

import i3
import yaml

from i3_utils import xrandr

""" i3-grid is a script to manage floating windows for the
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
    # Proper import for typings (object export from collections is deprecated)
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
     'GridOffset', 'DisplayMonitors', 'SocketPort', 'multis',
     'rc_file_name', 'DefaultResetPercentage'],
    [  # default values for config without rc file
     True, True, 0, {"Rows": 2, "Columns": 2},
     [0, 0, 0, 0], {"eDP1", "HDMI1", "VGA"}, 65433, 0,
     'i3gridrc', 75]
)}

# Logger for stdout
logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s |%(lineno)d]: %(message)s')
logger = logging.getLogger(__name__)

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
        port to listen for i3-grid middleware."""
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
                and i3.move("window", " position", "center")),
            "custom": (
                lambda *d: i3.resize("set", d[0], d[0])
                and i3.move("window", "position", "center")),
        }
        if isinstance(data, str):
            dispatcher[command](data)
        elif isinstance(data, Location):
            w = str(data.width) if data.width > 0 else "0"
            h = str(data.height) if data.height > 0 else "0"
            dispatcher[command](w, h)

    @staticmethod
    def i3_custom(cmd, id: str =None):
        _b = "i3-msg"  # Multiline string is necessary here (i3 encoding)
        return f"""{_b} [con_id="{id}"] {cmd}""" if cmd else (
                """{_b} {cmd}""")

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
            f"~/.config/i3grid/{rc}",
            f"~/.config/{rc}",
            f"~/.{rc}",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f".{rc}")]
        target_loc = None
        for loc in default_locs:
            if os.path.isfile(loc):
                target_loc = loc
                break

        if not target_loc:
            logger.warning(
                "No dotfile config found."
                " Add to ~/.i3gridrc or ~/.config/i3gridrc"
                " or ~/.config/i3grid/i3gridrc")

        with open(target_loc, "r") as f:
            config = yaml.safe_load(f)
        if not config or "Settings" not in config:
            raise ValueError(
                "Incorrect i3gridrc file sytax. Please"
                " follow yaml guidelines and example.")

        settings = config["Settings"]
        for key in settings:
            if settings[key] is not None:
                _CONFIG_GLOBALS[key] = settings[key]

    @staticmethod
    def on_the_fly_override(**kwargs) -> None:
        global _CONFIG_GLOBALS
        cmdline_serializer = {
            "rows": "Rows",
            "cols": "Columns",
            "target": "target",
            "perc": "DefaultResetPercentage",
            "port": "SocketPort",
            "offset": "GridOffset",
            "multis": "multis",
            "noresize": "AutoResize",
            "nofloat": "AutoConvertToFloat"}

        def offset_test(o, k):
            global _CONFIG_GLOBALS
            assert (
                len(o) <= 4
            ), "Incorrect Offset Arguments (Expected 4: t, r, b, l)"

            while len(o) != 4:
                o += [0]
            _CONFIG_GLOBALS[k] = [int(i) for i in o]
            _CONFIG_GLOBALS[k][1], _CONFIG_GLOBALS[k][3] = (
                _CONFIG_GLOBALS[k][3], _CONFIG_GLOBALS[k][1])

        _g_tst = {'rows', 'cols'}
        _auto_booleans = {'noresize', 'nofloat'}
        for arg in kwargs:
            if kwargs[arg] is None or arg not in cmdline_serializer:
                continue
            elif arg in _g_tst:
                _CONFIG_GLOBALS['DefaultGrid'][cmdline_serializer[arg]] = kwargs[arg]
            elif arg == 'target':
                _CONFIG_GLOBALS['SnapLocation'] = kwargs[arg]
            elif arg == 'offset':
                offset_test(kwargs[arg], cmdline_serializer[arg])
            elif arg in _auto_booleans:
                if kwargs[arg]:
                    _CONFIG_GLOBALS[cmdline_serializer[arg]] = False
            else:
                _CONFIG_GLOBALS[cmdline_serializer[arg]] = kwargs[arg]


class FloatUtils:
    """Utilities directly utilized
    by the float manager for i3 workspace
    metadata."""

    def __init__(self) -> None:
        self.active_output = None
        self.area_matrix, self.current_display = self._calc_metadata()
        assert len(self.current_display) > 0, "Incorrect Display Input"

    def assign_focus_node(self) -> None:
        tree = i3.get_tree()
        wkspc = [
            node for node in tree["nodes"]
            if node["name"] == self.current_display["output"]]
        assert len(wkspc) > 0, "window could not be found"
        self.iter = 0
        for w in wkspc:
            self.find_focused_window(w)
        if args.all is None:
            return

        wkspc = [k['nodes'] for k in wkspc[0]['nodes'] if k['name'] == 'content'][0]
        fcsd = [i for i in self.all_outputs if i['focused']][0]['name']

        def grep_nest(obj, key, key2, key3):  # TODO: change keys to kwargs
            arr = []

            def extract(obj, arr, key):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, (dict, list)):
                            extract(v, arr, key)
                        elif k == key:
                            arr.append((obj[key2], v, obj[key3]))
                elif isinstance(obj, list):
                    for item in obj:
                        extract(item, arr, key)
                return arr
            results = extract(obj, arr, key)
            return results

        data = [k for k in wkspc if k['name'] == fcsd][0]
        names = grep_nest(data, 'id', key2='name', key3="floating")
        self.current_windows = [i for i in names if i[0] and i[0] != fcsd]
        self.current_floating_windows = [i for i in self.current_windows]

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

        self.all_outputs = i3.get_workspaces()
        active = [i for i in self.all_outputs if i["focused"]][0]
        self.active_output = active['output']
        return total_size, active

    def get_wk_number(self) -> int:
        c_monitor = 0
        for display in self.displays:
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

    def get_i3_socket(self) -> i3.Socket:
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

    def xrandr_parser(self) -> 'Configuration':
        x = xrandr.XRandR()
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
        assert _CONFIG_GLOBALS['SnapLocation'] <= (
               rows * cols), "Incorrect Target in grid"
        # Check if target around border
        # if so, apply offset/(num rows or cols) (if resize)
        # if snap and border, apply full offset > + | -
        mode_defs = {
            "snap": lambda *d: _CONFIG_GLOBALS['GridOffset'][d[0]],
            "resize": lambda *xy: int(
                (_CONFIG_GLOBALS['GridOffset'][xy[0]] +
                 _CONFIG_GLOBALS['GridOffset'][xy[1]]) / (xy[2] or 1))}
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
            # per_offset = [int(i) for i in _CONFIG_GLOBALS['GridOffset']]
            return Location(width=_CONFIG_GLOBALS['GridOffset'][1],
                            height=_CONFIG_GLOBALS['GridOffset'][0])

        return Location(t_w, t_h)

    def get_offset(self, center: bool = True) -> Location:
        # No globals required (read only)
        # 1) Calculate monitor center
        # 2) Calculate window offset
        # 3) if tensors are intersecting: Monitor center - offset = true center
        display = self.area_matrix[self.workspace_num]
        window = self.get_target(self.focused_node)
        if center or _CONFIG_GLOBALS['SnapLocation'] == 0:
            # Abs center (2, 2)
            display_offset, target_offset = self.get_matrix_center(
                2, 2, display, window
            )
        else:
            # target = _CONFIG_GLOBALS['SnapLocation']
            # y, x adjusted for accessing matrix
            y, x = self.find_grid_axis()
            # 1 is the location (0 is the index)
            data = self.float_grid[y][x][1]  # naive
            return self.xrandr_calulator(data)  # monitor sync

        # Heigh is half of the respective monitor
        # The tensors are parallel hence, no summation.
        # local *centers (not abs)
        center_x = display_offset.width - target_offset.width
        center_y = display_offset.height - target_offset.height
        data = Location(center_x, center_y)
        return self.xrandr_calulator(data)

    def xrandr_calulator(self, orig_point: Location) -> Location:
        data = self.xrandr_parser()
        for n, monitor in data.outputs.items():
            monitor = monitor.__dict__
            if n == self.active_output:
                th = orig_point.height + monitor['position'][1]
                tw = orig_point.width + monitor['position'][0]
                return Location(tw, th)
        return orig_point

    def get_target(self, node: dict) -> None:
        return Location(width=node["rect"]["width"], height=node["rect"]["height"])

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

    def multi_pnt_calc(self):
        chosen_range = [int(i) for i in _CONFIG_GLOBALS['multis']]
        mid = (min(chosen_range), max(chosen_range))
        total_size = (_CONFIG_GLOBALS['DefaultGrid']['Rows'] *
                      _CONFIG_GLOBALS['DefaultGrid']['Columns'])
        assert (mid[0] <= total_size and
                mid[1] <= total_size), "Incorrect grid inputs"

        loc = [self.find_grid_axis(loc=mid[0]), self.find_grid_axis(loc=mid[1])]
        self.per_quadrant_dim = Location(
            (self.per_quadrant_dim.width +
             self.per_quadrant_dim.width * (loc[1][1] - loc[0][1])),
            (self.per_quadrant_dim.height +
             self.per_quadrant_dim.height * (loc[1][0] - loc[0][0])))
        self.make_resize()
        return self.cache_grid[loc[0][0]][loc[0][1]]

    def get_matrix_center(self, rows, cols, *windows: Location) -> Location:
        return [Location(int(window.width / rows), int(window.height / cols))
                for window in windows]


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
        cp = _CONFIG_GLOBALS['DefaultResetPercentage']
        Utils.dispatch_i3msg_com("custom", data=f"{cp}ppt")

    def snap_to_grid(self, **kwargs) -> None:
        """Moves the focused window to the target
        (default: 0) position in current grid (default: 2*2)"""
        true_center = kwargs['tc'] if 'tc' in kwargs else self.get_offset(
                      center=False,)
        Utils.dispatch_i3msg_com("move", true_center)

    def reset_win(self, **kwargs) -> None:
        """Moves to center and applies default tile
        to float properties (center, 75ppt)"""
        Utils.dispatch_i3msg_com(command="reset")

    def make_float(self, **kwargs) -> None:
        """Moves the current window into float mode if it is not float.
        If float, do nothing. Does not resize (feel free to combine) but i3
        does so by default sometimes (based on config and instance rules)."""
        Utils.dispatch_i3msg_com(command="float")

    def hide_scratchpad(self, **kwargs) -> None:
        id = kwargs['id'] if 'id' in kwargs else None
        dim = Utils.i3_custom("scratchpad show", id)
        Utils.dipatch_bash_command(dim)

    def multi_select(self, **kwargs) -> None:
        """Supports selection ranges
        that are continous and non-perpendicular."""
        if _CONFIG_GLOBALS['multis'] == 0:
            return self.move_to_center()
        elif len(_CONFIG_GLOBALS['multis']) == 1:
            return self.move_to_center()

        top_left = self.multi_pnt_calc()
        Utils.dispatch_i3msg_com("move", self.xrandr_calulator(top_left[1]))

    def all_override(self, commands: list, target: int) -> None:
        global _CONFIG_GLOBALS
        passive_actions = {'resize', 'float'}

        _CONFIG_GLOBALS['SnapLocation'] = 1
        for cmd in commands:
            for w in self.current_windows:
                dim = Utils.i3_custom("focus", w[1])
                Utils.dipatch_bash_command(dim)  # focus
                self.com_map[cmd]()  # Call user function (pass win id)
                if cmd not in passive_actions:  # iterate target
                    _CONFIG_GLOBALS['SnapLocation'] += 1


class FloatManager(Movements, Middleware):
    def __init__(self, **kwargs) -> None:
        """Manager > Movement > Calculator > Utility > Dispatch event"""
        super().__init__()
        # 1) Read config and merge globals
        Utils.read_config()
        # 2) Override to on the fly settings
        Utils.on_the_fly_override(**kwargs)
        # 3) Run initalizing commands
        self.post_commands()  # Sync to state
        # 4) Transform to global flags
        if _CONFIG_GLOBALS['AutoConvertToFloat']:
            self.make_float()
        if _CONFIG_GLOBALS['AutoResize']:
            self.make_resize()

        self.com_map = {c: e for c, e in zip(kwargs["commands"],
                        [self.move_to_center,
                        self.make_float,
                        self.make_resize,
                        self.snap_to_grid,
                        self.custom_resize,
                        self.hide_scratchpad,
                        self.reset_win,
                        self.start_server,
                        self.multi_select])}

        if kwargs['all'] is not None and kwargs['all']:  # All flag override
            self.all_override(kwargs['actions'], target=kwargs['all'])
            exit(0)

    def run_command(self, cmd: str, **kwargs) -> None:
        """Commands that must be refreshed on
        every action to sync state (C socket data transfer)"""
        if cmd not in self.com_map:
            raise KeyError("No corresponding run command to input:", cmd)
        self.post_commands()  # Resync to state
        threading.Thread(  # Thread middleware to speed up action
            target=self.dispatch_middleware,
            args=({"command": cmd, "modifying_node": self.focused_node,
                   'grid': self.cache_grid, 'monitors': self.displays},),
        ).start()  # Anonymous thread, since dataflow is unidirectional.
        self.com_map[cmd](**kwargs)

    def post_commands(self) -> None:
        self.workspace_num = self.get_wk_number()
        # Set the focused node
        self.assign_focus_node()
        self.float_grid = self.calculate_grid(
            _CONFIG_GLOBALS['DefaultGrid']["Rows"],
            _CONFIG_GLOBALS['DefaultGrid']["Columns"],
            self.area_matrix[self.workspace_num])


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
            logger.info("\nClosing i3-grid socket...")
        finally:
            exit(0)


if __name__ == "__main__":
    if "debug" in sys.argv:
        _debugger()
        exit(0)

    # start = datetime.datetime.now()
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

    # Manager can simply be a unpacked to args,
    # rather than manual seralizing into kwargs.
    manager = FloatManager(commands=comx, **args.__dict__,)
    for action in args.actions:
        manager.run_command(cmd=action)

    # end = datetime.datetime.now()
    # logger.info(f"Total Time: {end - start}")
    exit(0)
