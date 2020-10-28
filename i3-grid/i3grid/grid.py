#!/usr/bin/env python
# -*- coding: utf-8 -*-

# License: GPL-3.0
# Copyright (C) 2020 Sai Valla
# URL: https://github.com/justahuman1

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import collections
import json
import logging
import os
import socket
import subprocess
import sys
import re
import threading
from collections import namedtuple
from typing import Dict, List

try:
    from .xrandr import XRandR
    from .doc import Documentation
except ImportError:
    # cli
    from xrandr import XRandR
    from doc import Documentation

# Logger for stdout
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s %(levelname)s |i3-grid %(lineno)d]: %(message)s",
)
logger = logging.getLogger(__name__)

try:
    import i3ipc

    collectionsAbc = collections.abc
except ModuleNotFoundError:
    logger.critical("Missing i3-py module")
    exit(1)

# i3-grid is a module to manage floating windows for the
# i3 tiling window manager. The code is split into several classes, each
# isolating the logic respective to its name. The process flow is as follows:

#  1) FloatManager:      Manages the user input parsing and function dispatches

#  2) Movements:         Contains the functions that are directly
#                        called by the user to invoke window actions

#  3) MonitorCalculator: Manages the xrandr display settings
#                        to make display agnostic window decisions

#  4) FloatUtils:        The meta functions of the manager that
#                        directly assist the movements and calculator

#  5) Utils:             Additional utilities to abstract debugging,
#                        RPC calls, etc.

#  6) Middleware:        Manages socket connections for API bindings via
#                        library or command line

# Formatted with Black: https://github.com/psf/black

__author__ = "Sai Valla"
__version__ = "0.2.3b3"
__date__ = "2012-05-20"
__license__ = "GNU GPL 3"

# Custom Types
# The x and y coordinates of any X11 object
Location = namedtuple("Location", "width height")
# A vector of location objects
Tensor = List[Location]
# Represents the display monitor to their respective index
DisplayMap = Dict[int, Location]
# Single global dict -  shared interface for library & cli
BASE_CONFIG = {
    k: v
    for k, v in zip(
        [  # snake case keys are non-config keys for advanced tweaking
            "autoConvertToFloat",
            "autoResize",
            "snapLocation",
            "defaultGrid",
            "gridOffset",
            "socketPort",
            "multis",  # the multichannel flag
            "rc_file_name",  # change the name of the dotfile
            "defaultResetPercentage",
        ],
        [  # default values for config without rc file
            True,
            True,
            0,
            {"rows": 2, "columns": 2},
            [0, 0, 0, 0],
            65433,
            0,
            "i3gridrc",
            75,
        ],
    )
}
i3 = i3ipc.Connection()


class Middleware:
    """User middleware for additional event listening.
    Utilizes sockets for instance communication."""

    host = "127.0.0.1"  # Should not be mutated, hence class var

    def __init__(self,) -> None:
        super().__init__()

    def start_server(self, data_mapper: collectionsAbc.Callable) -> None:
        """Begins an AF_INET server at the given port to listen
        for i3-grid middleware. Dispatches result to data_mapper"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setblocking(1)
            logger.info(f"Binding to: {Middleware.host}/{BASE_CONFIG['socketPort']}")
            s.bind((Middleware.host, BASE_CONFIG["socketPort"]))
            s.listen()
            while True:
                # We only have one listener at a time. If we need
                # multiple listeners, we can add threading here.
                try:
                    conn, addr = s.accept()
                    with conn:
                        while True:
                            data = conn.recv(1024)
                            if not data:
                                break
                            data_mapper(data)
                            # Bidirectional data flow
                            # conn.sendall(data)
                except KeyboardInterrupt:
                    logger.info("Server Socket Closed")
                    break

    def dispatch_middleware(self, data: str, **kwargs) -> None:
        """Client Middleware to send data to server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Our socket is unidirectional for now. We can also allow for
            # user middleware via python/bash if necessary
            s.setblocking(1)
            try:
                s.connect((Middleware.host, BASE_CONFIG["socketPort"]))
            except (ConnectionRefusedError, BlockingIOError):
                return
            s.sendall(Middleware.str2bin(data))
            # If we want bidirectional data flow, we can have the client
            # listen to the server for additional events.
            # data = s.recv(1024)

    @staticmethod
    def str2bin(data: str, res_str: bool = False) -> "bytes":
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
    def dispatch_bash_command(command_str: str) -> str:
        """Dispatches command_str to a bash subshell."""
        if not command_str or command_str.strip() == "":
            raise ValueError("null command")
        out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        return out.stdout

    @staticmethod
    def dispatch_i3msg_com(
        command: str, data: Location = Location(1189, 652)
    ) -> list:
        """Internal function used to dispatch specific command strings to
        i3-ipc. Data may also be a string."""

        dispatcher = {
            # Dictionary of commands to execute with i3 comx
            "resize": lambda *d: i3.command(f"resize set {d[0]} {d[1]}"),
            "move": lambda *d: i3.command(f"move window position {d[0]} {d[1]}"),
            "float": lambda *d: i3.command("floating enable"),
            "center": lambda *d: i3.command("move window position center"),
            "reset": lambda *d: (
                i3.command(f"resize  set {d[0]}ppt {d[0]}ppt")
            ),
            "custom": (
                lambda *d: i3.command(f"resize set {d[0]} {d[0]}")
                and i3.command("move window position center")
            ),
        }
        if isinstance(data, str):
            return dispatcher[command](data)
        elif isinstance(data, Location):
            w = str(data.width) if data.width > 0 else "0"
            h = str(data.height) if data.height > 0 else "0"
            return dispatcher[command](w, h)

    @staticmethod
    def i3_custom(cmd: str, id: str = None) -> str:
        _b = "i3-msg"  # Multiline string is necessary here (i3 encoding)
        return f"""{_b} [con_id="{id}"] {cmd}""" if cmd else ("""{_b} {cmd}""")

    @staticmethod
    def read_config() -> None:
        """Reads the user i3gridrc file from $HOME."""
        global BASE_CONFIG
        rc = BASE_CONFIG["rc_file_name"]
        home = os.path.expanduser("~")
        default_locs = [
            f"{home}/.config/i3grid/{rc}",
            f"{home}/.config/{rc}",
            f"{home}/.{rc}",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f".{rc}"),
        ]
        target_loc = None
        for loc in default_locs:
            if os.path.isfile(loc):
                target_loc = loc
                break

        if not target_loc:
            logger.warning(
                "No dotfile config found."
                " Add to ~/.i3gridrc or ~/.config/i3gridrc"
                " or ~/.config/i3grid/i3gridrc"
            )
            return

        with open(target_loc, "r") as f:
            data = [line.strip().replace("\n", "") for line in f.readlines()]

        try:
            config = eval(
                "".join(
                    [
                        line.replace("true", "True").replace("false", "False")
                        for line in data
                        if not line.startswith("//")
                    ]
                )
            )
        except SyntaxError:
            raise ValueError(
                "Incorrect i3gridrc file sytax. Please"
                " follow jsonc guidelines and example."
            )

        for key in config:
            if config[key] is not None:
                BASE_CONFIG[key] = config[key]

    @staticmethod
    def on_the_fly_override(serialize: bool = False, **kwargs) -> None:
        global BASE_CONFIG
        cmdline_serializer = {
            "rows": "rows",
            "cols": "columns",
            "target": "target",
            "perc": "defaultResetPercentage",
            "port": "socketPort",
            "offset": "gridOffset",
            "multis": "multis",
            "noresize": "autoResize",
            "nofloat": "autoConvertToFloat",
        }
        if serialize:
            cmdline_serializer = {v: v for v in cmdline_serializer.values()}

        _g_tst = {"rows", "cols", "columns"}
        _auto_booleans = {"noresize", "nofloat"}
        for arg in kwargs:
            if kwargs[arg] is None or arg not in cmdline_serializer:
                continue
            elif arg in _g_tst:
                BASE_CONFIG["defaultGrid"][cmdline_serializer[arg]] = kwargs[arg]
            elif arg == "target" or arg == "snapLocation":
                BASE_CONFIG["snapLocation"] = kwargs[arg]
            elif arg == "offset" or arg == "gridOffset":
                BASE_CONFIG[cmdline_serializer[arg]] = Utils.offset_test(
                    kwargs[arg], cmdline_serializer[arg]
                )
            elif arg in _auto_booleans:
                if kwargs[arg]:
                    BASE_CONFIG[cmdline_serializer[arg]] = False
            else:
                BASE_CONFIG[cmdline_serializer[arg]] = kwargs[arg]

    @staticmethod
    def offset_test(o, k) -> List[int]:
        tmp_arr = []
        assert len(o) <= 4, "Incorrect Offset Arguments (Expected 4: t, r, b, l)"
        while len(o) != 4:
            o += [0]
        tmp_arr = [int(i) for i in o]
        tmp_arr[1], tmp_arr[3] = (
            tmp_arr[3],
            tmp_arr[1],
        )
        return tmp_arr


class FloatUtils:
    """Utilities directly utilized
    by the float manager for i3 workspace
    metadata."""

    def __init__(self) -> None:
        self.active_output_name = None
        self.area_matrix, self.current_display = self._calc_metadata()
        # self.focus_tree = None
        self.current_windows = self.focus_tree = None
        # assert len(self.current_display) > 0, "Incorrect Display Input"

    def update_config(self, val: dict) -> bool:
        """Float configration lock manager. Allows
        for multiple user config declarations otf."""
        assert isinstance(val, dict), "Config value must be a dict."
        _similarity = set(BASE_CONFIG) - set(val)
        assert (
            len(_similarity) == 0
        ), f"Config value requires the additional keys: {_similarity}"
        Utils.on_the_fly_override(serialize=True, **val)  # Validate update
        self.cache_grid = None  # Update cache
        return True

    def assign_focus_node(self, filter_bypass=False) -> None:
        # self.focus_tree = self.focus_tree or i3.get_tree()
        self.focus_tree = i3.get_tree()
        self.focused_node = self.focus_tree.find_focused().__dict__
        self.all_windows = [
            (con.name, con.id)
            for con in self.focus_tree
            if con.window and con.parent.type != "dockarea"
        ]
        self.current_windows = [
            (con.id, con.name, con.floating)
            for con in self.focus_tree.find_focused().workspace().descendants()
        ]

    def _calc_metadata(self) -> (DisplayMap, dict):
        self.displays = [o.__dict__ for o in i3.get_outputs()]
        # Widths * Lengths (seperated to retain composition for children)
        total_size = {}
        monitor_cnt = 0
        for display in self.displays:
            if display["name"].startswith("xroot"):
                continue
            display_screen_location = Location(
                width=display["rect"].width, height=display["rect"].height,
            )
            total_size[monitor_cnt] = display_screen_location
            monitor_cnt += 1

        active = [i for i in i3.get_workspaces() if i.focused][0]
        self.active_output_name = active.output
        return total_size, active.__dict__

    def get_wk_number(self) -> int:
        c_monitor = 0
        for display in self.displays:
            if not display["name"].startswith("xroot"):
                if self.match(display):
                    break
                c_monitor += 1
        return c_monitor

    def match(self, display: dict) -> bool:
        validations = [
            ["name", "output"],
            ["current_workspace", "name"],
            "rect",
        ]
        for val in validations:
            if val == "rect":
                if display["rect"].width != self.current_display["rect"].width:
                    return False
            elif display[val[0]] != self.current_display[val[1]]:
                return False
        return True

    def xrandr_parser(self) -> "Configuration":
        """Low level communicator with the xrandr
        module. Loads the overall monitor grid offset."""
        x = XRandR()
        x.load_from_x()
        return x.configuration


class MonitorCalculator(FloatUtils):
    def __init__(self,) -> None:
        super().__init__()
        self.xrandr_config = self.cache_grid = None

    def calc_monitor_offset(
        self, mode: str, point: Location = None  # , loc: int = None
    ) -> Location:
        """Internal offset manager to apply offsets
        to given quadrant based on operation."""
        rows = BASE_CONFIG["defaultGrid"]["rows"]
        cols = BASE_CONFIG["defaultGrid"]["columns"]
        assert BASE_CONFIG["snapLocation"] <= (
            rows * cols
        ), "Incorrect Target; not in grid"
        if mode == "resize":
            normalize = lambda *xy: int(
                (BASE_CONFIG["gridOffset"][xy[0]] + BASE_CONFIG["gridOffset"][xy[1]])
                / (xy[2] or 1)
            )
            r_l = normalize(3, 1, cols)
            t_b = normalize(0, 2, rows)
            return Location(point.width - r_l, point.height - t_b)
        elif mode == "snap":
            return Location(
                width=BASE_CONFIG["gridOffset"][1], height=BASE_CONFIG["gridOffset"][0],
            )
        return point

    def get_offset(self, center: bool = True) -> Location:
        """Read only operation to determine offset.
        1) Calculate monitor center
        2) Calculate window offset
        3) If Tensors are intersecting: monitor center - offset = true center"""
        display = self.area_matrix[self.workspace_num]
        window = self.get_target(self.focused_node)
        if center or BASE_CONFIG["snapLocation"] == 0:
            # Abs center (2, 2)
            display_offset, target_offset = self.get_matrix_center(
                2, 2, display, window
            )
            logger.info(display_offset)
            logger.info(target_offset)
            # data = self.calculate_snap_loc()
            # return self.xrandr_calulator(data)  # monitor sync
        else:
            # y, x adjusted for accessing matrix
            data = self.calculate_snap_loc()
            return self.xrandr_calulator(data)  # monitor sync

        # Heigh is half of the respective monitor
        # The tensors are parallel hence, no summation.
        # Calculates local window *centers (not abs)
        center_x = display_offset.width - target_offset.width
        center_y = display_offset.height - target_offset.height
        data = Location(center_x, center_y)
        return self.xrandr_calulator(data)

    def xrandr_calulator(self, orig_point: Location) -> Location:
        """Uses the xrandr module to calculate the offset per monitor
        in relevance to the overall figure. Caches per run."""
        if not self.xrandr_config:
            self.xrandr_config = self.xrandr_parser()
        for n, monitor in self.xrandr_config.outputs.items():
            monitor = monitor.__dict__
            if n == self.active_output_name:
                th = orig_point.height + monitor["position"][1]
                tw = orig_point.width + monitor["position"][0]
                return Location(tw, th)
        return orig_point

    def get_target(self, node: dict) -> Location:
        return Location(width=node["rect"].width, height=node["rect"].height)

    def find_grid_axis(self, loc: int = None) -> tuple:
        """Translate front-end grid location to DisplayMap axis"""
        loc = loc or BASE_CONFIG["snapLocation"]
        return divmod(loc - 1, BASE_CONFIG["defaultGrid"]["columns"])

    def calculate_grid(self, rows: int, cols: int, display: Location):
        """Sets the instance attributes for quadrant sizing. The istance attributes
        are used in various calulations and command dispatchment."""
        # Account for window size offset (grid quadrant size - offset/(rows | cols))
        main_loc = Location(int(display.width / cols), int(display.height / rows))
        self.per_quadrant_dim = self.calc_monitor_offset("resize", main_loc)

    def calculate_snap_loc(self, loc: tuple = None) -> Location:
        """Lazily calculate position on DisplayMap rather than
        generating the complete grid (as done in v0.2.3b3)"""
        # (int, int) of grid location
        snap_location = loc or self.find_grid_axis()
        # Offset calculation is offloaded to a seperate function
        offset = self.calc_monitor_offset("snap")
        height = (snap_location[0] * self.per_quadrant_dim.height) + offset.height
        width = (snap_location[1] * self.per_quadrant_dim.width) + offset.width
        return Location(width, height)

    def multi_pnt_calc(self) -> Location:
        """Calculation for user multipoints. Uses the max min
        procedure to determine top left and bottom right position."""
        chosen_range = [int(i) for i in BASE_CONFIG["multis"]]
        mid = (min(chosen_range), max(chosen_range))
        total_size = (
            BASE_CONFIG["defaultGrid"]["rows"] * BASE_CONFIG["defaultGrid"]["columns"]
        )
        assert (
            0 < mid[0] <= total_size and mid[1] <= total_size
        ), "Incorrect grid inputs"

        loc = [
            self.find_grid_axis(loc=mid[0]),
            self.find_grid_axis(loc=mid[1]),
        ]
        self.per_quadrant_dim = Location(
            (
                self.per_quadrant_dim.width
                + self.per_quadrant_dim.width * (loc[1][1] - loc[0][1])
            ),
            (
                self.per_quadrant_dim.height
                + self.per_quadrant_dim.height * (loc[1][0] - loc[0][0])
            ),
        )
        self.make_resize()  # Multis requries additional resize
        return self.calculate_snap_loc(loc[0])  # Returns the top left point

    def get_matrix_center(self, rows, cols, *windows: Location) -> Location:
        return [
            Location(int(window.width / rows), int(window.height / cols))
            for window in windows
        ]

    def title_to_id(self, title_or_id: str) -> str:
        if title_or_id is None or title_or_id[0] == "":
            return None

        # print(self.current_windows[0])

        title_or_id = " ".join(title_or_id).strip('"')
        if title_or_id in self.current_windows[0]:
            print("Matched title/ID")
        # if not exact match, check regex

        # print(title_or_id)
        # print("Converting title to id")
        exit()

        # Check if id (number regex)
        # if title_or_id
        pass


class Movements(MonitorCalculator):
    def __init__(self,) -> None:
        super().__init__()

    def move_to_center(self, **kwargs) -> list:
        """Moves the focused window to
        the absolute window center (corresponds to
        target=0)"""
        return Utils.dispatch_i3msg_com(command="center")

    def make_resize(self, **kwargs) -> list:
        target_size = self.per_quadrant_dim
        return Utils.dispatch_i3msg_com("resize", data=target_size)

    def custom_resize(self, **kwargs) -> list:
        """Resize window to custom screen percentage"""
        cp = BASE_CONFIG["defaultResetPercentage"]
        return Utils.dispatch_i3msg_com("custom", data=f"{cp}ppt")

    def snap_to_grid(self, **kwargs) -> list:
        """Moves the focused window to the target
        (default: 0) position in current grid (default: 2*2)"""
        true_center = kwargs.get("tc", self.get_offset(center=False,))
        return Utils.dispatch_i3msg_com("move", true_center)

    def reset_win(self, **kwargs) -> list:
        """Moves to center and applies default tile
        to float properties (center, {config}ppt)"""
        Utils.dispatch_i3msg_com(
            command="reset",
            data=str(BASE_CONFIG["defaultResetPercentage"]),
        )
        self.post_commands()  # Resync to window state
        return self.snap_to_grid()

    def make_float(self, **kwargs) -> list:
        """Moves the current window into float mode if it is not
        float. If float, do nothing. Does not resize but i3 does so
        by default sometimes (based on config and instance rules)."""
        return Utils.dispatch_i3msg_com(command="float")

    def hide_scratchpad(self, **kwargs) -> list:
        """Hides the current window (if
        scratchpad) or to kwargs `id` window."""
        id = kwargs.get("id", None)
        dim = Utils.i3_custom("scratchpad show", id)
        return Utils.dispatch_bash_command(dim)

    def focus_window(self, **kwargs) -> list:
        """Focuses on the given kwargs 'id' window"""
        id = kwargs.get("id", None)
        if not id:
            raise ValueError("No `id` kwargs given for window focus.")
        dim = Utils.i3_custom("focus", kwargs["id"])
        return Utils.dispatch_bash_command(dim)  # focus

    def multi_select(self, **kwargs) -> list:
        """Supports selection ranges
        that are continous and non-perpendicular."""
        # TODO: Extend to id -> Prefocus and dispatch and focus back to orig
        if BASE_CONFIG["multis"] == 0 or len(BASE_CONFIG["multis"]) == 1:
            return self.move_to_center()

        top_left = self.multi_pnt_calc()
        return Utils.dispatch_i3msg_com("move", self.xrandr_calulator(top_left))

    def all_override(self, commands: list, **kwargs) -> List[tuple]:
        """The overrider for the run command to optimize for
        multiple actions. Automatically syncs the i3 state
        between each given command (from commandse). All kwargs are passed
        to the run function. Kwargs:
        floating {boolean}: Applies the actions to only the floating windows."""
        global BASE_CONFIG
        _tmp_loc = BASE_CONFIG["snapLocation"]
        self.post_commands(passive=False)
        # all override for only floating win
        if "floating" in kwargs and kwargs["floating"]:
            self.current_windows = [
                d for d in self.current_windows if d[2] == "user_on"
            ]

        BASE_CONFIG["snapLocation"] = 1  # Temporary change to data
        for w in self.current_windows:
            for cmd in commands:
                self.focus_window(id=w[0])  # focus win
                self.run(cmd, all=True, **kwargs)  # dispatch cmd
                if cmd not in self.passive_actions:  # iterate target
                    BASE_CONFIG["snapLocation"] += 1
        BASE_CONFIG["snapLocation"] = _tmp_loc  # Restore state

        return self.current_windows


class FloatManager(Movements, Middleware):
    def __init__(self, **kwargs) -> None:
        """Manager > Movement > Calculator > Utility > Dispatch event.
        Accepts kwargs: `all` (for all window actions), `actions` (list of
        initial actions to run, if all) """
        super().__init__()
        # 1) Read config and merge globals
        Utils.read_config()
        # 2) Override to on the fly settings
        Utils.on_the_fly_override(serialize=False, **kwargs)
        # 3) Run initalizing commands
        self.passive_actions = {"resize", "float", "hide", "listen", "center"}
        self.workspace_num = self.get_wk_number()
        self._TERMSIG = kwargs.get("all", False)
        self.filter_mode = kwargs.get("filter", None)
        floating = kwargs.get("floating", False)

        # Filter bypass
        # if self.filter_mode is not None:
        #     pass

        # self.post_commands(all_key=self._TERMSIG)  # Sync to state
        kwargs["commands"] = kwargs.get("commands", list(Documentation.actions))
        self.com_map = {
            c: e
            for c, e in zip(
                kwargs["commands"],
                [
                    self.move_to_center,
                    self.make_float,
                    self.make_resize,
                    self.snap_to_grid,
                    self.custom_resize,
                    self.hide_scratchpad,
                    self.reset_win,
                    self.start_server,
                    self.multi_select,
                ],
            )
        }

        if self._TERMSIG or floating:  # 4) Transform to global flags
            if "actions" not in kwargs:
                raise ValueError("Missing kwargs `commands` for all_override")
            self.all_override(kwargs["actions"], floating=floating)
            self._TERMSIG = True  # Exit point for CLI
            return

    def run_flags(self) -> None:
        if BASE_CONFIG["autoConvertToFloat"]:
            self.make_float()
        if BASE_CONFIG["autoResize"]:
            self.make_resize()

    def run(self, cmd: str, **kwargs) -> list:
        """The main command dispatcher. Used to abstract state syncronization.
        All kwargs are passed to the action. Accepts commands that must be
        refreshed on every action to sync state (C socket data transfer)"""
        if cmd not in self.com_map:
            raise KeyError("No corresponding run command to input:", cmd)

        passive = True if cmd in self.passive_actions else False
        # Filter is a global identifier (takes input str > i3 ID)
        kwargs["id"] = self.title_to_id(self.filter_mode)
        if not kwargs.get("all", False):
            self.post_commands(passive=passive)  # sync state
        if not passive:
            self.run_flags()  # run user flags, if any
        threading.Thread(  # Thread middleware to speed up action
            target=self.dispatch_middleware,
            args=(
                {
                    "command": cmd,
                    # "modifying_node": self.focused_node,
                    # "monitors": self.displays,
                    # "windows": self.current_windows,
                },
            ),
        ).start()  # Anonymous thread, since dataflow is unidirectional.
        self.com_map[cmd](**kwargs)
        return None

    def post_commands(self, passive=False) -> None:
        """Runs all the state related commands with
        proper cache maintanence to minimize rpc."""
        if not passive:
            self.assign_focus_node()

        self.calculate_grid(
            BASE_CONFIG["defaultGrid"]["rows"],
            BASE_CONFIG["defaultGrid"]["columns"],
            self.area_matrix[self.workspace_num],
        )
