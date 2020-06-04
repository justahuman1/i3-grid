import i3grid
import unittest
import warnings
import time

# TODO: Per class unit tests
# TODO: CLI Integration Test


def input_manager(prompt):
    """Small input formatter"""
    print()
    confirm = ". [y/N]: "
    accepts = {"y", "yes", "1"}
    usr_val = input(prompt + confirm)
    print("-" * 30)
    if usr_val.lower().strip() in accepts:
        return 1
    return 0


def mc_gen():
    return i3grid.FloatManager(), i3grid.BASE_CONFIG


class TestManager(unittest.TestCase):
    """Unit test for the FloatManager class (library)
    class per each action and flags."""

    def test_1center(self):
        manager, conf = mc_gen()
        conf["DefaultGrid"] = {"Rows": 2, "Columns": 2}
        conf["AutoResize"] = False
        manager.update_config(conf)
        manager.run(cmd="center")
        self.assertEqual(input_manager("The window has been centered"), 1)

    def test_2screen_percentage(self):
        manager, conf = mc_gen()
        sizes = [33, 75, 50]
        for s in sizes:
            conf["DefaultResetPercentage"] = s
            manager.update_config(conf)
            manager.run(cmd="csize")
            self.assertEqual(
                input_manager(f"The window is {s}% of the screen ratio"), 1
            )

    def test_3resize_snap(self):
        manager, conf = mc_gen()
        conf["DefaultGrid"] = {"Rows": 3, "Columns": 1}
        conf["SnapLocation"] = 2
        manager.update_config(conf)
        manager.run(cmd="resize")
        manager.run(cmd="snap")
        self.assertEqual(input_manager("The window is in target 2 in a 1*3 grid"), 1)

    def test_4multipoint_strech(self):
        manager, conf = mc_gen()
        conf["DefaultGrid"] = {"Rows": 4, "Columns": 4}
        conf["multis"] = [1, 14]
        manager.update_config(conf)
        manager.run(cmd="multi")
        self.assertEqual(input_manager("The window is half the screen width"), 1)

    def test_5offsets(self):
        manager, conf = mc_gen()
        t_off = [0] * 4
        loc = [1] * 4
        strs = ["top", "right", "bottom", "left"]
        conf["DefaultGrid"] = {"Rows": 1, "Columns": 1}
        for i in range(len(t_off)):
            t_off[i] = 20
            conf["GridOffset"] = t_off
            conf["SnapLocation"] = loc[i]
            manager.update_config(conf)
            manager.run(cmd="resize")
            manager.run(cmd="snap")
            t_off[i] = 0
            self.assertEqual(
                input_manager(f"The window is only offset from the {strs[i]}"), 1
            )

    def test_6hide(self):
        input("\nThis test hides the current window, if scratchpad only.")
        manager, conf = mc_gen()
        conf["AutoConvertToFloat"] = conf["AutoResize"] = False
        manager.update_config(conf)
        manager.run(cmd="hide")
        self.assertEqual(
            input_manager(f"If the current window is a scratchpad, it was hidden"), 1
        )

    def test_7floating(self):
        input("\nOpen two more windows. Make one floating and one tiled. Press Enter to continue.")
        manager, conf = mc_gen()
        conf["DefaultGrid"] = {"Rows": 2, "Columns": 2}
        manager.update_config(conf)
        manager.all_override(commands=["snap"], floating=True)
        self.assertEquals(
            input_manager("Only the floating windows were snapped sequentially in a grid"), 1
        )

    def test_8all(self):
        # TODO: Add floating only test
        input("\nOpen other windows for this test. Press Enter to continue")
        manager, conf = mc_gen()
        conf["DefaultGrid"] = {"Rows": 2, "Columns": 2}
        manager.update_config(conf)
        manager.all_override(commands=["snap"])
        self.assertEquals(
            input_manager("All windows were snapped sequentially in a grid"), 1
        )

    def test_9listener(self):
        input(
            "\nPress Ctrl+C once the socket opens to complete test. Press Enter to continue"
        )
        manager, conf = mc_gen()
        conf["AutoConvertToFloat"] = conf["AutoResize"] = False
        manager.update_config(conf)
        manager.run("listen", data_mapper=print)
        self.assertEquals(input_manager("The socket opened and closed gracefully"), 1)

    def test_10reset(self):
        manager = i3grid.FloatManager()
        manager.run(cmd="reset")
        self.assertEqual(
            input_manager("The window was reset to 75% of screen (i3 default)"), 1
        )


if __name__ == "__main__":
    # Block socket warning
    warnings.simplefilter("ignore", ResourceWarning)
    unittest.main(warnings="ignore")
    unittest.main()
