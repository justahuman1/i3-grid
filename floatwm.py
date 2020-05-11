import os
import argparse
import subprocess
import sys
from collections import namedtuple
from typing import Dict, List

import i3
import yaml

from doc import Documentation

# Custom Types
# The x and y coordinates of any X11 object
Location = namedtuple('Location', 'width height')
# A vector of location objects
Tensor = List[Location]
# Represents the display monitor to their respective index
DisplayMap = Dict[int, Location]

# Globals used for config
AUTO_FLOAT_CONVERT = False
SNAP_LOCATION = 0
RC_FILE_NAME = 'floatrc'
DEFAUlT_GRID = {'rows': 2,'cols':2 }
DISPLAY_MONITORS = {
    "eDP1",
    "HDMI1",
    "VGA",
}

# TODO: replace global variables with rc file
# TODO: handle multiple monitor (behind summation) offset
# TODO: add grid options

class Utils:
    def __init__(self, ):
        super().__init__()

    @staticmethod
    def dipatch_bash_command(command_str: str) -> str:
        if (not command_str or
           command_str.strip() == ""): raise ValueError("null command")

        out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        return out.stdout

    @staticmethod
    def dispatch_i3msg_com(command: str, data:Location=Location(1189, 652)):
        # Immutable location tuple accounts for mutation error
        if not isinstance(data, (list, tuple)) and len(data) == 2:
            raise ValueError("Incorrect data type/length for i3 command")
        w = str(data.width) if data.width > 0 else '0'
        h = str(data.height) if data.height > 0 else '0'
        if command == 'resize':
            # 1189, 652 is a standard i3 window size for floating nodes
            # Data should be a len(Vector) == 2 (width, height)
            return i3.resize('set', w, h)
        if command == 'move':
            print(f'w: {w}, h: {h}"')
            return i3.move('window', 'position', w, h)
        if command == 'float':
            return i3.floating('enable')


    @staticmethod
    def get_cmd_args(elem: int=None) -> (Location, int):
        try:
            if elem:
                if elem > len(sys.argv[1:]):
                    return None
                elif len(sys.argv[1:]) < 2:
                    return [4, 4][elem]
                return int(sys.argv[elem])
            else:
                return [int(i) for i in sys.argv[1:]] or [4, 4]
        except ValueError:
            return [4, 4]

    @staticmethod
    def read_config():
        global DISPLAY_MONITORS, RC_FILE_NAME
        global AUTO_FLOAT_CONVERT, DEFAUlT_GRID
        global SNAP_LOCATION

        default_locs = [
            f'~/.config/i3float/{RC_FILE_NAME}'
            f'~/.config/{RC_FILE_NAME}',
            f'~/.{RC_FILE_NAME}',
            os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f'.{RC_FILE_NAME}')
        ]
        target_loc = None
        for loc in default_locs:
            if os.path.isfile(loc):
                target_loc = loc
                break

        if not target_loc:
            raise ValueError("No dotfile config found. " \
                             "Add to ~/.floatrc or ~/.config/floatrc " \
                             "or ~/.config/i3float/floatrc")

        with open(target_loc, 'r') as f:
            config = yaml.safe_load(f)
        if not config or 'Settings' not in config:
            raise ValueError("Incorrect floatrc file sytax. Please follow yaml guidelines and example.")

        monitors_yml_key = 'DisplayMonitors'
        grid_yml_key = 'DefaultGrid'
        auto_yml_key = 'AutoConvertToFloat'
        snap_yml_key = 'SnapLocation'
        grid_yml_syn = ['Rows', 'Columns']
        settings = config['Settings']

        if monitors_yml_key in settings:
            DISPLAY_MONITORS = tuple(m for m in settings[monitors_yml_key])
        if grid_yml_key in settings:
            DEFAUlT_GRID = {
                    'rows': settings[grid_yml_key][grid_yml_syn[0]],
                    'cols': settings[grid_yml_key][grid_yml_syn[1]],
            }
        if auto_yml_key in settings:
            AUTO_FLOAT_CONVERT = True if settings[auto_yml_key] else False

        if snap_yml_key in settings:
            if isinstance(settings[snap_yml_key], int):
                SNAP_LOCATION = settings[snap_yml_key]
            else:
                raise ValueError("Unexpected Snap location data type (expected int)")

    @staticmethod
    def on_the_fly_override(**kwargs):
        global DISPLAY_MONITORS, RC_FILE_NAME
        global AUTO_FLOAT_CONVERT, DEFAUlT_GRID
        global SNAP_LOCATION
        # if 'row' in kwargs:
        pass


class FloatUtils:
    def __init__(self):
        self.area_matrix, self.current_display = self._calc_metadata()
        assert len(self.current_display) > 0, "Incorrect Display Input"

    def assign_focus_node(self):
        tree = i3.get_tree()
        # for node in tree:
        wkspc = [node for node in tree['nodes']
                if node['name'] == self.current_display['output']]
        assert len(wkspc) > 0, "window could not be found"
        # wkspc = wkspc[0]
        self.iter = 0
        for w in wkspc:
            self.find_focused_window(w)

    def find_focused_window(self, node):
        # DFS to find the current window
        self.iter += 1
        if not isinstance(node, dict): return
        if node['focused']:
            self.focused_node = node
            return

        if (len(node['nodes']) != 0) or (len(node['floating_nodes']) != 0):
            target_nodes = node['nodes'] + node['floating_nodes']
            for root in target_nodes: self.find_focused_window(root)
        else: return


    def _calc_win_resize(self):
        pass

    def _calc_metadata(self) -> (DisplayMap, dict):
        self.displays = i3.get_outputs()

        # Widths * Lengths (seperated to retain composition for children)
        total_size = {}
        monitor_cnt = 0
        for display in self.displays:
            if display['name'] not in DISPLAY_MONITORS:
                continue
            display_screen_location = Location(
                    width=display['rect']['width'],
                    height=display['rect']['height'])
            total_size[monitor_cnt] = display_screen_location
            monitor_cnt += 1

        active = [i for i in i3.get_workspaces() if i['focused']][0]
        return total_size, active

    def get_wk_number(self):
        c_monitor = 0
        for display in self.displays:
            if display['name'] in DISPLAY_MONITORS:
                if self.match(display): break
                c_monitor += 1
        return c_monitor

    def match(self, display):
        validations = [
            ['name', 'output'],
            ['current_workspace', 'name'],
            'rect'
        ]
        for val in validations:
            if val == 'rect':
                if (display[val]['width'] !=
                    self.current_display[val]['width']):
                    return False
            elif display[val[0]] != self.current_display[val[1]]:
                return False
        return True

    def get_i3_socket(self):
        socket = i3.Socket()


class MonitorCalculator(FloatUtils):
    def __init__(self, ):
        super().__init__()

    def get_offset(self, window: Location, target: Location) -> Location:
        # 1) Calculate monitor center
        # 2) Calculate window offset
        # 3) Monitor center - offset = true center
        # 3 if) tensors are intersecting
        display_offset, target_offset = self.get_screen_center(
                window, target)
        # Heigh is half of the respective monitor
        # The tensors are parallel hence, no summation.
        center_x = display_offset.width - target_offset.width
        center_y = display_offset.height - target_offset.height
        return Location(center_x, center_y)

    def calculate_grid(self, rows, cols):
        pass


    def get_screen_center(self, *windows: Location) -> Location:
        return [Location(int(window.width/2), int(window.height/2))
                for window in windows]

class Movements(MonitorCalculator):
    def __init__(self, ):
        super().__init__()

    def move_to_center(self, *args):
        workspace_num = self.get_wk_number()
        # Get the focused node
        self.assign_focus_node()
        # print(self.focused_node)

        # we call the focused node the target
        target_pos = Location(width=self.focused_node['rect']['width'],
                 height=self.focused_node['rect']['height'])
        # print('target:', target_pos)

        # True center (accounting for multiple displays)
        # The height vector is difficult to calculate due to XRandr
        # offsets (that can extend in any direction).
        true_center = self.get_offset(window=self.area_matrix[workspace_num],
                                      target=target_pos)
        # TODO
        # Apply offset (user preference (due to polybar, etc.))
        # Apply screen offset (XRandr)

        # Dispatch final command
        # if input("Run? >> ") == 'y':
        Utils.dispatch_i3msg_com(command="move", data=true_center)

    def move_to_grid(self, *args):
        pass

    def make_float(self):
        Utils.dispatch_i3msg_com(command='float')


class FloatManager(Movements):
    available_commands = ['center', 'snap', 'float']
    # Manager > Movement > Calculator > Utility > Dispatch event
    def __init__(self, **kwargs):
        super().__init__()
        # 1) Read config and merge globals
        Utils.read_config()
        # 2) Override on the fly settings
        Utils.on_the_fly_override(**kwargs)
        # If not float, make float -> <movement>
        if AUTO_FLOAT_CONVERT:
            self.make_float()
        executors = [
            self.move_to_center,
            self.move_to_grid,
            self.make_float,
        ]
        self.commands = {
            c:e for c,e in zip(
            FloatManager.available_commands,
            executors)}

    def run_command(self, cmd, *args):
        if cmd not in self.commands:
            raise KeyError("No corresponding run command to input:", cmd)
        print(cmd)
        print(self.commands)

        # self.commands[cmd](*args)



def debugger():
    print("Entering debug mode. Evaluating input:")
    while 1:
        cmd = input('>>> ')
        print(eval(cmd))

if __name__ == "__main__":
    if "debug" in sys.argv:
        debugger()
        exit(0)

    doc = Documentation()
    parser = doc.build_parser(choices=FloatManager.available_commands)
    args = parser.parse_args()

    for action in args.actions:
        FloatManager().run_command(cmd=action)


