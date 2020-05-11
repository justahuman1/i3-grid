import argparse

class Documentation:
    def __init__(self, ):
        super().__init__()

    def action_help(self):
        self.actions = {
            'center': "center the focused window to a float window",
            'float': "toggle the float of a window (overrides config file for otf movements)",
            'resize': "resize focused window (if float)",
        }

        action_parser = argparse.ArgumentParser()


