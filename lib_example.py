import i3grid


def p(desc):
    """Small formatter"""
    print(desc)
    if len(input("Leave blank to continue. 'q' to quit:\n\t>> ")) != 0:
        exit()
    print('-'*10)

# Instantiate the main manager which
# controls the command dispatchment process.
manager = i3grid.FloatManager(check=True)
p("Instantiated Float Manager")

# Run a command on the following window
manager.run('center')
p("Centered the current Window.")
# Default will center current window

# Change the default configurations
# This can be done even before creating the
# manager instance
new_config = i3grid.BASE_CONFIG

# Check the possible configurations you can make
# print(new_config.keys())

new_config['DefaultGrid'] = {'Rows': 3, 'Columns': 1}
# In this example, Rows * Columns = 3
# SnapLocation must be less than this number.
new_config['SnapLocation'] = 2

# Update the keys (Will throw error if misconfigured)
manager.update_config(new_config)

# Snap to location 2 as configured above
manager.run('resize')
manager.run('snap')
p("Created a 3x1 grid and placed in snap 2")

# Reset size (Can be configured via DefaultResetPercentage)
manager.run('csize')
p("Reset the window to default i3 float size")

# Apply action to all windows in workspace
manager.all_override(commands=['float', 'resize', 'snap'])
p("Applied float, resize, and snap to all windows in workspace")

# You can also interact with scratchpads,
# manage offsets, and use the event sockets
# for customized callbacks.
print("Example Completed!")
