#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ARandR -- Another XRandR GUI: https://github.com/chrysn/arandr
# Modified for i3-grid - 2020
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
from functools import reduce
from math import pi


class Size(tuple):
    """2-tuple of width and height that can be
    created from a '<width>x<height>' string"""

    def __new__(cls, arg):
        if isinstance(arg, str):
            arg = [int(x) for x in arg.split("x")]
        arg = tuple(arg)
        assert len(arg) == 2
        return super(Size, cls).__new__(cls, arg)

    width = property(lambda self: self[0])
    height = property(lambda self: self[1])

    def __str__(self):
        return "%dx%d" % self


class NamedSize:
    """Object that behaves like a size, but has an additional name attribute"""

    def __init__(self, size, name):
        self._size = size
        self.name = name

    width = property(lambda self: self[0])
    height = property(lambda self: self[1])

    def __str__(self):
        if "%dx%d" % (self.width, self.height) in self.name:
            return self.name
        return "%s (%dx%d)" % (self.name, self.width, self.height)

    def __iter__(self):
        return self._size.__iter__()

    def __getitem__(self, i):
        return self._size[i]

    def __len__(self):
        return 2


class Position(tuple):
    """2-tuple of left and top that can be created from a '<left>x<top>' string"""

    def __new__(cls, arg):
        if isinstance(arg, str):
            arg = [int(x) for x in arg.split("x")]
        arg = tuple(arg)
        assert len(arg) == 2
        return super(Position, cls).__new__(cls, arg)

    left = property(lambda self: self[0])
    top = property(lambda self: self[1])

    def __str__(self):
        return "%dx%d" % self


class Geometry(tuple):
    """4-tuple of width, height, left and top that can be created from an XParseGeometry style string"""

    # FIXME: use XParseGeometry instead of an own incomplete implementation
    def __new__(cls, width, height=None, left=None, top=None):
        if isinstance(width, str):
            width, rest = width.split("x")
            height, left, top = rest.split("+")
        return super(Geometry, cls).__new__(
            cls, (int(width), int(height), int(left), int(top)))

    def __str__(self):
        return "%dx%d+%d+%d" % self

    width = property(lambda self: self[0])
    height = property(lambda self: self[1])
    left = property(lambda self: self[2])
    top = property(lambda self: self[3])

    position = property(lambda self: Position(self[2:4]))
    size = property(lambda self: Size(self[0:2]))


class Rotation(str):
    """String that represents a rotation by a multiple of 90 degree"""

    def __init__(self, _original_me):
        super().__init__()
        if self not in ("left", "right", "normal", "inverted"):
            raise Exception("No know rotation.")

    is_odd = property(lambda self: self in ("left", "right"))
    _angles = {"left": pi / 2, "inverted": pi, "right": 3 * pi / 2, "normal": 0}
    angle = property(lambda self: Rotation._angles[self])

    def __repr__(self):
        return "<Rotation %s>" % self


LEFT = Rotation("left")
RIGHT = Rotation("right")
INVERTED = Rotation("inverted")
NORMAL = Rotation("normal")
ROTATIONS = (NORMAL, RIGHT, INVERTED, LEFT)


class Feature:
    PRIMARY = 1


class XRandR:
    DEFAULTTEMPLATE = ["#!/bin/sh", "%(xrandr)s"]

    configuration = None
    state = None

    def __init__(self, display=None, force_version=False):
        """Create proxy object and check for xrandr at `display`. Fail with
        untested versions unless `force_version` is True."""
        self.environ = dict(os.environ)
        if display:
            self.environ["DISPLAY"] = display

        version_output = self._output("--version")
        supported_versions = ["1.2", "1.3", "1.4", "1.5"]
        if (not any(x in version_output for x in supported_versions) and
           not force_version):
            raise Exception("XRandR %s required." % "/".join(supported_versions))

        self.features = set()
        if " 1.2" not in version_output:
            self.features.add(Feature.PRIMARY)

    def _get_outputs(self):
        assert self.state.outputs.keys() == self.configuration.outputs.keys()
        return self.state.outputs.keys()

    outputs = property(_get_outputs)

    #################### calling xrandr ####################

    def _output(self, *args):
        proc = subprocess.Popen(
            ("xrandr",) + args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=self.environ,)
        ret, err = proc.communicate()
        status = proc.wait()
        if status != 0:
            raise Exception("XRandR returned error code %d: %s" % (status, err))
        return ret.decode("utf-8")

    def _run(self, *args):
        self._output(*args)

    def load_from_x(self):  # FIXME -- use a library
        self.configuration = self.Configuration(self)
        self.state = self.State()

        screenline, items = self._load_raw_lines()

        self._load_parse_screenline(screenline)

        for headline, details in items:
            if headline.startswith("  ") or headline == "":
                continue  # a currently disconnected part of the screen i can't currently get any info out of

            headline = headline.replace("unknown connection", "unknown-connection")
            hsplit = headline.split(" ")
            output = self.state.Output(hsplit[0])
            assert hsplit[1] in ("connected", "disconnected", "unknown-connection")

            output.connected = hsplit[1] in ("connected", "unknown-connection")

            primary = False
            if "primary" in hsplit:
                if Feature.PRIMARY in self.features:
                    primary = True
                hsplit.remove("primary")

            if not hsplit[2].startswith("("):
                active = True
                geometry = Geometry(hsplit[2])

                if hsplit[4] in ROTATIONS:
                    current_rotation = Rotation(hsplit[4])
                else:
                    current_rotation = NORMAL
            else:
                active = False
                geometry = None
                current_rotation = None

            output.rotations = set()
            for rotation in ROTATIONS:
                if rotation in headline:
                    output.rotations.add(rotation)

            currentname = None
            for detail, w, h in details:
                name, _mode_raw = detail[0:2]
                mode_id = _mode_raw.strip("()")
                try:
                    size = Size([int(w), int(h)])
                except ValueError:
                    raise Exception(
                        "Output %s parse error: modename %s modeid %s."
                        % (output.name, name, mode_id))
                if "*current" in detail:
                    currentname = name
                for x in ["+preferred", "*current"]:
                    if x in detail:
                        detail.remove(x)

                for old_mode in output.modes:
                    if old_mode.name == name:
                        if tuple(old_mode) != tuple(size):
                            pass
                        break
                else:
                    output.modes.append(NamedSize(size, name=name))

            self.state.outputs[output.name] = output
            self.configuration.outputs[
                output.name
            ] = self.configuration.OutputConfiguration(
                active, primary, geometry, current_rotation, currentname)

    def _load_raw_lines(self):
        output = self._output("--verbose")
        items = []
        screenline = None
        for line in output.split("\n"):
            if line.startswith("Screen "):
                assert screenline is None
                screenline = line
            elif line.startswith("\t"):
                continue
            elif line.startswith(2 * " "):  # [mode, width, height]
                line = line.strip()
                if reduce(bool.__or__, [line.startswith(x + ":") for x in "hv"]):
                    line = line[-len(line) : line.index(" start") - len(line)]
                    items[-1][1][-1].append(line[line.rindex(" ") :])
                else:  # mode
                    items[-1][1].append([line.split()])
            else:
                items.append([line, []])
        return screenline, items

    def _load_parse_screenline(self, screenline):
        assert screenline is not None
        ssplit = screenline.split(" ")

        ssplit_expect = [
            "Screen", None, "minimum", None,
            "x", None, "current", None, "x",
            None, "maximum", None, "x", None]
        assert all(a == b for (a, b) in zip(ssplit, ssplit_expect) if b is not None)

        self.state.virtual = self.state.Virtual(
            min_mode=Size((int(ssplit[3]), int(ssplit[5][:-1]))),
            max_mode=Size((int(ssplit[11]), int(ssplit[13]))),)
        self.configuration.virtual = Size((int(ssplit[7]), int(ssplit[9][:-1])))

    class State:
        """Represents everything that can not be set by xrandr."""

        virtual = None

        def __init__(self):
            self.outputs = {}

        def __repr__(self):
            return "<%s for %d Outputs, %d connected>" % (
                type(self).__name__,
                len(self.outputs),
                len([x for x in self.outputs.values() if x.connected]),)

        class Virtual:
            def __init__(self, min_mode, max_mode):
                self.min = min_mode
                self.max = max_mode

        class Output:
            rotations = None
            connected = None

            def __init__(self, name):
                self.name = name
                self.modes = []

            def __repr__(self):
                return "<%s %r (%d modes)>" % (
                    type(self).__name__,
                    self.name,
                    len(self.modes),)

    class Configuration:
        """
        Represents everything that can be set by xrandr
        (and is therefore subject to saving and loading from files)
        """

        virtual = None

        def __init__(self, xrandr):
            self.outputs = {}
            self._xrandr = xrandr

        def __repr__(self):
            return "<%s for %d Outputs, %d active>" % (
                type(self).__name__,
                len(self.outputs),
                len([x for x in self.outputs.values() if x.active]),)

        def commandlineargs(self):
            args = []
            for output_name, output in self.outputs.items():
                args.append("--output")
                args.append(output_name)
                if not output.active:
                    args.append("--off")
                else:
                    if (Feature.PRIMARY in self._xrandr.features and
                       output.primary):
                            args.append("--primary")
                    args.append("--mode")
                    args.append(str(output.mode.name))
                    args.append("--pos")
                    args.append(str(output.position))
                    args.append("--rotate")
                    args.append(output.rotation)
            return args

        class OutputConfiguration:
            def __init__(self, active, primary, geometry, rotation, modename):
                self.active = active
                self.primary = primary
                if active:
                    self.position = geometry.position
                    self.rotation = rotation
                    if rotation.is_odd:
                        self.mode = NamedSize(
                            Size(reversed(geometry.size)), name=modename)
                    else:
                        self.mode = NamedSize(geometry.size, name=modename)

            size = property(
                lambda self: NamedSize(Size(reversed(self.mode)), name=self.mode.name)
                if self.rotation.is_odd
                else self.mode)
