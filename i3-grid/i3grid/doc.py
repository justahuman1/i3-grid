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

from argparse import (
    SUPPRESS,
    Action,
    ArgumentParser,
    HelpFormatter,
    RawTextHelpFormatter,
)


class CustomFormatter(HelpFormatter):
    """Custom Formatter used for documentation
    in order to add groups and include metadata
    for each command."""

    def _format_action_invocation(self, action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                # if the Optional doesn't take a value, format the value
                parts.extend(action.option_strings)
            else:
                # if the Optional takes a value, format as is
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append("%s %s" % (option_string, args_string))
            if sum(len(s) for s in parts) < self._width - (len(parts) - 1) * 2:
                return ", ".join(parts)
            else:
                return ",\n  ".join(parts)


class NoAction(Action):
    """Parser default setting changes to
    help action calling. Allows for individual
    groups per namespace."""

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("default", SUPPRESS)
        kwargs.setdefault("nargs", 0)
        super(NoAction, self).__init__(**kwargs)

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        pass


class Documentation:
    """The help menu for
    the FloatManager. Presented with
    the '-h' flag."""
    actions = {
            "center": "Center the focused window to a float window",
            "float": (
                "Toggle the float of a window (overrides config file for"
                " otf movements)"
            ),
            "resize": "Resize focused window (if float)",
            "snap": (
                "Runs grid placement of window (can be combined with all"
                " other actions). Flag args include rows, cols, and target"
            ),
            "csize": "Resize the window into a custom size of screen (1-100)",
            "hide": "Hide the current window to scratchpad (if scratchpad)."
            " Can be combined with 'all' flag to clear floating windows in workspace",
            "reset": "Resets the focused window into the middle occupying"
            " 75ppt (i3 default) screen space",
            "listen": (
                "Socket Listener (sole action) for event binding in native"
                " Python and command line (Listens on port flag or"
                " default: 65433)"
            ),
            "multi": ("Stretch a window across a range of numbers (Use flag 'multis')"),
        }

    def __init__(self,) -> None:
        super().__init__()
        _rc_def = "(default in rc file)"
        _slc_txt = lambda ax: f"Number of {ax} slices in screen grid {_rc_def}"
        _ffa = lambda action: f"Flag for action: '{action}'"
        _ova = lambda auto: f"Override auto {auto} on the fly to be false"
        _appl = lambda w: f"Applies the action(s) to all {w} windows in current workspace"
        self.flags = {
            "cols": {"type": "int", "help": _slc_txt("col")},
            "rows": {"type": "int", "help": _slc_txt("row")},
            "offset": {
                "type": "str",
                "action": "append",
                "nargs": "+",
                "help": "On the fly offset per window"
                " {Array[top, right, bottom, left]} | Ex: --offset 10 0"
                " (Can take upto 4 integers. Less than 4 fills the remaining"
                " values with 0. This example is the same as: --offset 10 0 0 0)",
            },
            "perc": {
                "type": "int",
                "help": f"{_ffa('csize')} (Percentage of screen {{int}}[1-100])",
            },
            "target": {
                "type": "int",
                "help": f"The grid location to snap the window to {_rc_def}",
            },
            "multis": {
                "type": "str",
                "action": "append",
                "nargs": "+",
                "help": f"The range of numbers to strech the window across."
                " Ex (4x4 grid): '1 2 3 4' or '1 4' (horizontal) or '1 5 9 13'"
                "or '1 13' (vertical)  or '1 8' (2 horizontal rows)",
            },
            "port": {
                "type": "int",
                "help": "The port number to listen for i3-grid events (Overrid"
                "ing port for server requires overriding for the client also)",
            },
        }
        self.state_flags = {
            "all": _appl('windows') ,
            "floating": _appl('floating windows'),
            "noresize": _ova('resize'),
            "nofloat": _ova('float'),
        }

    def build_parser(self, choices: list) -> ArgumentParser:
        parser = ArgumentParser(
            prog="i3grid",
            description="i3grid: Manage your floating windows with ease.",
            formatter_class=CustomFormatter,
        )
        parser.register("action", "none", NoAction)
        parser.add_argument(
            "actions",
            metavar="<action>",
            type=str,
            nargs="+",
            choices=choices,
            help=self.action_header(),
        )

        for n, flag in self.flags.items():
            parser.add_argument(
                f"--{n}",
                type=eval(flag["type"]) if "type" in flag else None,
                nargs=flag["nargs"] if "nargs" in flag else None,
                help=flag["help"],
            )
        for n, desc in self.state_flags.items():
            parser.add_argument(f"--{n}", action="store_true", help=desc)

        group = parser.add_argument_group(title="Actions")
        for action, desc in Documentation.actions.items():
            group.add_argument(action, help=desc, action="none")
        return parser

    def action_header(self) -> str:
        return """Actions are the functions to execute on the current window.
                  Order of operations matters here. For Example:
                  "python i3-grid.py snap float --target 3"
                  We can assume that this command is for a tiled window
                  (as the user passed an option to make the window float).
                  This will try to snap the window to grid position 3 but
                  fails, as it is not floating. The proper order would be:
                  "python i3-grid.py float snap --target 3".
                  A minimum of one action is required to run the script."""

    def action_choices(self) -> str:
        help_str = "Actions:\n"
        for action, desc in Documentation.actions.items():
            help_str += f"{action}\t{desc}\n"

        return help_str
