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

    def __init__(self,) -> None:
        super().__init__()
        self.actions = {
            "center": "Center the focused window to a float window",
            "float": (
                "Toggle the float of a window (overrides config file for"
                "otf movements). Optional 'all' flag to float all windows"
                "in sepecific workspace)"
            ),
            "resize": "Resize focused window (if float)",
            "snap": (
                "Runs grid placement (can be combined with all"
                "other actions). Arguments include rows, cols, and target"
            ),
            "csize": "Resize the window into a custom size of screen (1-100)",
            "reset": "Resets the focused window into the middle occupying"
            " 75ppt (i3 default) screen space",
            "listen": (
                "Socket Listener (sole action) for event binding in native"
                " Python and command line (Listens on port flag or"
                " default: 65433)"
            ),
        }
        _rc_def = "(default in rc file)"
        _slc_txt = lambda ax: f"Number of {ax} slices in screen grid {_rc_def}"
        _ffa = lambda action: f"Flag for action: '{action}'"
        _ova = lambda auto: f"Override auto {auto} on the fly {{bool}}"
        self.flags = {
            "cols": {"type": "int", "help": _slc_txt("col")},
            "rows": {"type": "int", "help": _slc_txt("row")},
            "all": {
                "type": "int",
                "help": "Applies the action (permitted only for float"
                "and snap) to all windows in the int workspace",
            },
            "offset": {
                "type": "str",
                "action": "append",
                "nargs": "+",
                "help": "On the fly offset per window",
            },
            "perc": {
                "type": "int",
                "help": f"{_ffa('csize')} (Percentage of screen {{int}}[1-100])",
            },
            "target": {
                "type": "int",
                "help": f"The grid location to snap the window to {_rc_def}",
            },
            "noresize": {"type": "bool", "help": _ova("resize")},
            "nofloat": {"type": "bool", "help": _ova("float")},
            "port": {
                "type": "int",
                "help": "The port number to listen for floatwm events (Overrid"
                "ing port for server requires overriding for the client also)",
            },
        }

    def build_parser(self, choices: list) -> ArgumentParser:
        parser = ArgumentParser(
            description="Manage your floating windows with ease.",
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

        for flag in self.flags:
            parser.add_argument(
                f"--{flag}",
                type=eval(self.flags[flag]["type"]),
                nargs=self.flags[flag]["nargs"]
                if "nargs" in self.flags[flag]
                else None,
                help=self.flags[flag]["help"],
            )

        group = parser.add_argument_group(title="Actions")
        for action, desc in self.actions.items():
            group.add_argument(action, help=desc, action="none")
        return parser

    def action_header(self) -> str:
        return """Actions are the functions to execute on the current window.
                  Order of operations matters here. For Example:
                  "python floatwm.py center float --target 3"
                  We can assume that this command is for a tiled window
                  (as the user passed an option to make the window float).
                  This will try to center the window to grid position 3 but
                  fails, as it is not floating. The proper order would be:
                  "python floatwm.py float center --target 3"
                  A minimum of one action is required to run the script."""

    def action_choices(self) -> str:
        help_str = "Actions:\n"
        for action, desc in self.actions.items():
            help_str += f"{action}\t{desc}\n"

        return help_str
