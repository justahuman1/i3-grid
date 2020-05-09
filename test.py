import floatwm
import subprocess, sys

# FloatManager Test


def center_test():
    man = floatwm.FloatManager()


# Utils Unit test

class Unit:
    def __init__(self, ):
        super().__init__()

    def execute_bash(self, command_str):
        print("2 cmd")
        print(command_str)
        return floatwm.Utils.dipatch_bash_command(command_str)
        # if (not command_str or
        #    command_str.strip() == ""): raise ValueError("null command")
        # out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        # return out.stdout


class UtilsTest(Unit):
    def __init__(self, ):
        super().__init__()

def cmd_line_test():
    # args = '4 4'  # test a 4x4 floating grid
    # print(floatwm.Utils.get_cmd_args())
    print("Entering debug mode. Evaluating input.")
    print(
    Unit().execute_bash("python floatwm.py 0 0")
    )
    # print(floatwm.Utils.get_cmd_args(0))


def metadata_test():
    util = floatwm.FloatUtils()
    # total_size, active_monitor = util.calc_metadata()
    print(util.area_matrix)
    print(util.current_display)

# center_test()
cmd_line_test()
