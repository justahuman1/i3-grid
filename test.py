import floatwm
import subprocess, sys


class Unit:
    """Base Unit class for unit testing"""
    def __init__(self, ):
        super().__init__()

    def execute_bash(self, command_str):
        return floatwm.Utils.dipatch_bash_command(command_str)
        # if (not command_str or
        #    command_str.strip() == ""): raise ValueError("null command")
        # out = subprocess.run(command_str.split(" "), stdout=subprocess.PIPE)
        # return out.stdout

# FloatManager Test

class ManagerTest(Unit):
    def __init__(self, ):
        super().__init__()

    def center_test(self, ):
       (floatwm
        .FloatManager()
        .run_command('center'))

    def grid_test(self, target):
        (floatwm
         .FloatManager(target=target)
         .run_command('snap'))


# Utils Unit test



class UtilsTest(Unit):
    def __init__(self, ):
        super().__init__()

    def cmd_line_test(self):
        args = '2 2'  # test a 4x4 floating grid
        Unit().execute_bash(f"python floatwm.py {args}")

    def yaml_load_test(self):
        floatwm.Utils.read_config()

def help_test():
    print(floatwm.Utils.dipatch_bash_command('python floatwm.py'))


def metadata_test():
    util = floatwm.FloatUtils()
    # total_size, active_monitor = util.calc_metadata()
    print(util.area_matrix)
    print(util.current_display)

# center_test()
# cmd_line_test()
# ManagerTest().center_test()
help_test()
# UtilsTest().yaml_load_test()
