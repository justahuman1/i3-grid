import i3, subprocess
from typing import List
import sys

DISPLAY_MONITORS = {
    "eDP1",
    "HDMI1",
    "VGA",
}
# Custom Types
Tensor = List[int]

class Utils:
    def __init__(self, ):
        super().__init__()

    @staticmethod
    def dipatch_bash_command(command_str: str) -> str:
        print("In dis")
        if (not command_str or
           command_str.strip() == ""): raise ValueError("null command")
        # print(command_str.split(" "))
        out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        return out.stdout

    @staticmethod
    def make_i3msg_command(command: str, data:Tensor=[1189, 652]):
        # 1189, 652 is a standard i3 window size for floating nodes
        if command == 'resize':
            # Data should be a len(Vector) == 2 (width, height)
            if isinstance(data, (list, tuple)) and len(data) == 2:
                return f"i3-msg resize set {data[0]} {data[1]}"
            else:
                raise ValueError("Incorrect data type/length for i3 command")

    @staticmethod
    def get_cmd_args(elem=None):
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


class FloatUtils:
    def __init__(self):
        self.area_matrix, self.current_display = self._calc_metadata()
        assert len(self.current_display) > 0, "Incorrect Display Input"
        self.current_display = self.current_display[0]

    def _calc_metadata(self):
        self.displays = i3.get_outputs()

        # Widths * Lengths (seperated to retain composition for children)
        total_size = [[], []]
        for display in self.displays:
            if display['name'] not in DISPLAY_MONITORS:
                continue
            total_size[0] += [display['rect']['width']]
            total_size[1] += [display['rect']['height']]
        active = [i for i in i3.get_workspaces() if i['focused']]
        # print(active)
        return total_size, active

    def get_i3_socket(self):
        socket = i3.Socket()


class MonitorCalculator:
    def __init__(self, ):
        super().__init__()

    def get_offset(self, window_tensor, monitor_tensor):
        # 1) Calculate monitor center
        # 2) Calculate window offset
        # 3) Monitor center - offset = true center
        pass


    def get_screen_center(self, width:int, height:int) -> Tensor :
        return [int(width/2), int(height/2)]


class FloatManager(FloatUtils, MonitorCalculator):
    def __init__(self, rows=2, cols=2, target=0):
        super().__init__()
        if target == 0:
            self.move_to_center()
        self.rows = rows
        self.cols = cols
        self.target = target

    def move_to_center(self):
        # workspace_num = self.get_wk_number()
        # x_positioning = 0
        # for i  in range(len(self.displays)):
        #     if (self.displays[i]['name'] in DISPLAY_MONITORS) and (i < workspace_num):
        #         x_positioning += self.area_matrix[0][i]
        # x_positioning += self.get_screen_center(
        #         self.current_display['rect']['width'],
        #         self.current_display['rect']['height'])[0]
        self.get_current_window()

        # print(workspace_num)
        # print(x_positioning)


    def get_current_window(self):
        tree = i3.get_tree()
        # print(self.current_display['output'])
        # for node in tree:
        wkspc = [node for node in tree['nodes']
                if node['name'] == self.current_display['output']]
        assert len(wkspc) > 0, "window could not be found"
        # wkspc = wkspc[0]
        self.iter = 0
        # print(len(wkspc))
        for w in wkspc:
            # print(type(w))
            self.find_focused_window(w)
        print(self.iter)
        print(self.focused_node)
        cmd = Utils.make_i3msg_command(command="resize")
        Utils.dipatch_bash_command(command_str=cmd)

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

        # for d, t in in zip(display, self.current_display):
            # if

if __name__ == "__main__":
    if "debug" in sys.argv:
        print("Entering debug mode. Evaluating input:")
        while 1:
            cmd = input('>>> ')
            print(eval(cmd))

    # print(sys.argv)
    # print(i3)
    # div = 4
