#!/usr/bin/env python

import i3grid


def p(desc):
    """Small formatter"""
    print(desc)
    if len(input("Leave blank to continue. 'q' to quit:\n\t>> ")) != 0:
        exit()
    print("-" * 10)


# Instantiate the main manager which
# controls the command dispatchment process.
manager = i3grid.FloatManager(all=False, floating=False)
p("Instantiated Float Manager")

# Run a command on the following window
manager.run("center")
p("Centered the current Window.")
# Default will center current window

# Update the default configurations
new_config = i3grid.BASE_CONFIG

# Check the possible configurations that can be made
# print(new_config.keys())

new_config["defaultGrid"] = {"rows": 3, "columns": 1}
# In this example, Rows * Columns = 3
# SnapLocation must be less than this number.
new_config["snapLocation"] = 2

# Update the keys (Will throw error if misconfigured)
manager.update_config(new_config)

# Snap to location 2 as configured above
manager.run("resize")
manager.run("snap")
p("Created a 3x1 grid and placed in snap 2")

# Reset size (Can be configured via DefaultResetPercentage)
manager.run("csize")
p("Reset the window to default i3 float size")

# Apply action to all windows in workspace (floating param filters out the tiled windows)
manager.all_override(commands=["float", "resize", "snap"], floating=False)
p("Applied float, resize, and snap to all windows in workspace")

# Extra examples
# Listening to i3-grid events
# The data mapper is a callback function
# that receives some data. Ex:
# def data_mapper(*args: List[bytes]) --> None:
print("Opening socket. Press Ctrl+C to exit..")
manager.run("listen", data_mapper=print)
p("Opened and closed the i3-grid listener socket")

# You can also interact with scratchpads,
# manage offsets, and use the event sockets
# for customized callbacks.
print("Example Completed!")
