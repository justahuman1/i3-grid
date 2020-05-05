import floatwm

# FloatManager Test


def center_test():
    man = floatwm.FloatManager()

# Utils Unit test


def metadata_test():
    util = floatwm.FloatUtils()
    # total_size, active_monitor = util.calc_metadata()
    print(util.area_matrix)
    print(util.current_display)

center_test()
