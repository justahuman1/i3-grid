import subprocess
import sys
import json
import math
import os
from os.path import expanduser
from tempfile import TemporaryFile


def backtick(command):
    """
    Equivalent of Bourne shell's backtick
    See http://www.python.org/doc/2.5.1/lib/node534.html
    """
    from subprocess import Popen, PIPE

    print("backtick: command='%s'\n" % command)
    value = Popen(["bash", "-c", command], stdout=PIPE).communicate()[0].rstrip()
    # print "returning '%s'\n" % value
    return value


def get_workspace():
    # this also works:
    # i3-msg -t get_workspaces|jq '.[]|select(.focused == true)|.rect'
    output = backtick("i3-msg -t get_workspaces")
    data = json.loads(output.decode())
    data = sorted(data, key=lambda k: k["name"])
    for i in data:
        if i["focused"]:
            r = i["rect"]
            print(
                "get_workspace: returning '%s': '%d' '%d'\n"
                % (i["name"], r["width"], r["height"])
            )
            return i["name"], r["width"], r["height"]


def get_window():
    jq_prog = "recurse(.nodes[],.floating_nodes[])|select(.focused)|.rect"
    output = backtick("i3-msg -t get_tree | jq '%s' 2>/dev/null" % jq_prog)
    data = json.loads(output.decode())
    print(
        "get_window: returning x,y,width,height=%d %d %d %d"
        % (data["x"], data["y"], data["width"], data["height"])
    )
    return data["x"], data["y"], data["width"], data["height"]


if len(sys.argv) < 4:
    print("Error not enough arguments - need x, y, width, height")
    print(
        "x, y: -1 for unchanged, -2 for left/down a width/height, -3 for right/up a width/height, -4 for rhs/bottom, -5 for centre"
    )
    print(
        "width/height: -1, 0 or blank for unchanged; -2 for half-screen; -3 for third; -4 for quarter"
    )
    print("positive width & height are % of screen")
    sys.exit(1)

new_x = int(sys.argv[1])
new_y = int(sys.argv[2])
new_width = int(sys.argv[3])
new_height = int(sys.argv[4])

ws_name, ws_width, ws_height = get_workspace()
print("workspace name width height = (%s %d %d)\n" % (ws_name, ws_width, ws_height))
old_x, old_y, old_width, old_height = get_window()
print(
    "window x y width height = (%d %d %d %d)\n" % (old_x, old_y, old_width, old_height)
)
# old_x, old_y, old_width, old_height = -1, -1, -1, -1

if new_width == -1:
    new_width = old_width
elif new_width == -2:
    new_width = ws_width / 2
elif new_width == -3:
    new_width = ws_width / 3
elif new_width == -4:
    new_width = ws_width / 4
else:
    new_width = ws_width * new_width / 100

if new_height == -1:
    new_height = old_height
elif new_height == -2:
    new_height = ws_height / 2
elif new_height == -3:
    new_height = ws_height / 3
elif new_height == -4:
    new_height = ws_height / 4
else:
    new_height = ws_height * new_height / 100

if new_x == -1:
    new_x = old_x
elif new_x == -2:
    new_x = old_x - new_width
elif new_x == -3:
    new_x = old_x + new_width
elif new_x == -4:
    new_x = ws_width - new_width
elif new_x == -5:
    new_x = (ws_width - new_width) / 2

if new_y == -1:
    new_y = old_y
elif new_y == -2:
    new_y = old_y - new_height
elif new_y == -3:
    new_y = old_y + new_height
elif new_y == -4:
    new_y = ws_height - new_height
elif new_y == -5:
    new_y = (ws_height - new_height) / 2

if new_x < 0:
    new_x = 0
# if new_x + new_width > ws_width: new_x = ws_width - new_width

if new_y < 0:
    new_y = 0
# if new_y + new_height > ws_height: new_y = ws_height - new_height

if new_x != old_x or new_y != old_y:
    backtick("i3-msg -- move position %d px %d px" % (new_x, new_y))
if new_width != old_width or new_height != old_height:
    backtick("i3-msg -- resize set %d px %d px" % (new_width, new_height))

sys.exit(0)
