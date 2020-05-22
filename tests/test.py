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

import subprocess
import sys
import time

from ..i3-grid import i3
from doc import Documentation


class Unit:
    """Base Unit class for unit testing"""

    def __init__(self,):
        super().__init__()

    def execute_bash(self, command_str):
        return i3.Utils.dipatch_bash_command(command_str)


# FloatManager Test


class ManagerTest(Unit):
    def __init__(self,):
        super().__init__()

    def center_test(self,):
        (i3.FloatManager().run_command("center"))

    def grid_test(self, target):
        (i3.FloatManager(target=target).run_command("snap"))

    def main_run_emulator(self):
        doc = Documentation()
        comx = list(doc.actions)
        manager = i3.FloatManager(commands=comx)
        manager.run_command(cmd="snap")


# Utils Unit test


class UtilsTest(Unit):
    def __init__(self,):
        super().__init__()

    def cmd_line_test(self):
        args = "2 2"  # test a 4x4 floating grid
        Unit().execute_bash(f"python i3.py {args}")

    def yaml_load_test(self):
        i3.Utils.read_config()


def help_test():
    val = i3.Utils.dipatch_bash_command("python floatwm.py")
    help_err = "Incorrect main body (triggering a function without value)"
    assert val is not None, help_err


def metadata_test():
    util = i3.FloatUtils()
    # total_size, active_monitor = util.calc_metadata()
    print(util.area_matrix)
    print(util.current_display)


class IntegrationTests:
    def __init__(self,):
        super().__init__()

    def map_command_chain(self,):
        comx = ["float", "center", "snap"]


class SocketTest:
    """Test Socket client and server
    for i3 messaging & event listening."""

    def __init__(self,):
        super().__init__()

    def start_server(self):
        self.server = i3.Middleware()
        self.server.start_server(data_mapper=SocketTest.test_function)

    @staticmethod
    def test_function(data):
        print("In custom middleware function.")
        # Data manipulations and event handling
        data = str(data)
        time.sleep(5)
        transformed_data = data.lower()
        print(transformed_data)


# TODO - Add commands to dictionary and consider pytest
# Currently, pytest is not being used because the code is still pretty small
# center_test()
# cmd_line_test()
# ManagerTest().center_test()
# help_test()
# UtilsTest().yaml_load_test()
SocketTest().start_server()
