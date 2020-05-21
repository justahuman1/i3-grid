#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""License:
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
import subprocess
import sys
import time

import floatwm
from doc import Documentation


class Unit:
    """Base Unit class for unit testing"""

    def __init__(self,):
        super().__init__()

    def execute_bash(self, command_str):
        return floatwm.Utils.dipatch_bash_command(command_str)


# FloatManager Test


class ManagerTest(Unit):
    def __init__(self,):
        super().__init__()

    def center_test(self,):
        doc = Documentation()
        comx = list(doc.actions)
        (floatwm.FloatManager(commands=comx).run_command("center"))

    def grid_test(self, target):
        (floatwm.FloatManager(target=target).run_command("snap"))

    def main_run_emulator(self):
        doc = Documentation()
        comx = list(doc.actions)
        manager = floatwm.FloatManager(commands=comx)
        manager.run_command(cmd="snap")


# Utils Unit test


class UtilsTest(Unit):
    def __init__(self,):
        super().__init__()

    def cmd_line_test(self):
        args = "2 2"  # test a 4x4 floating grid
        Unit().execute_bash(f"python floatwm.py {args}")

    def yaml_load_test(self):
        floatwm.Utils.read_config()


def help_test():
    val = floatwm.Utils.dipatch_bash_command("python floatwm.py")
    help_err = "Incorrect main body (triggering a function without value)"
    assert val is not None, help_err


def metadata_test():
    util = floatwm.FloatUtils()
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
        self.server = floatwm.Middleware()
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
# Futhermore, it is hard to assert window values with pytest,
# as the result is dependent on external data flow.
tests = {
    "center": {
        "desc": "Centering the current window",
        "def": lambda: ManagerTest().center_test(),
        "post_msg": "The current window is centered",
    },
    "cmd_line": {
        "desc": "Testing command line parser",
        "def": lambda: UtilsTest().cmd_line_test(),
        "post_msg": "No errors were printed to stdout",
    },
    "help": {
        "desc": "Testing the command line help menu",
        "def": help_test,
        "post_msg": "A help menu was printed above",
    },
    "config": {
        "desc": "Testing yaml user configuration reading",
        "def": lambda: UtilsTest().yaml_load_test(),
        "post_msg": "No errors were printed to stdout",
    },
    # "socket": {
    #     "desc": "Testing middleware socket server",
    #     "post_msg": "No errors were printed to stdout",
    #     "def": lambda: UtilsTest().yaml_load_test(),
    # },
}


def runner():
    results = {}.fromkeys(['passed', 'skipped', 'failed'], [])
    print('-'*10, "Running  i3-grid tests", '-'*10)
    print("Respond to the questions with T (true) or F (false)", end="\n")
    if input("Run tests? [y/N] > ").lower() != 'y':
        print("Exiting testing..")
        exit(0)
    for name, test in tests.items():
        print(f"Test Name: {name}")
        print(f"Test Description: {test['desc']}")
        if input('Run current test? [y/N] > ').lower() == 'y':
            test['def']()
            print(test['post_msg'])
            res = input("[t/F] > ")
            if res.lower() == 't':
                results['passed'] += [name]
            else:
                results['failed'] += [name]
        else:
            results['skipped'] += [name]
        print('-'*20)

    print()
    print('='*20)
    for o_type in results:
        print(f"{o_type.title()} Tests: ")
        for r in results[o_type]:
            print(r)

    print('='*10, "Summary", '='*10)
    print(f"Passed Tests: {len(results['passed'])}")
    print(f"Failed Tests: {len(results['failed'])}")
    print(f"Skipped Tests: {len(results['skipped'])}")
    print('='*10, "Summary", '='*10)


if __name__ == "__main__":
    runner()
