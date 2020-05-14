from argparse import (SUPPRESS, Action, ArgumentParser, HelpFormatter,
                      RawTextHelpFormatter)


class CustomFormatter(HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                # if the Optional doesn't take a value, format the value
                parts.extend(action.option_strings)
            else:
                # if the Optional takes a value, format as is
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s %s' % (option_string, args_string))
            if sum(len(s) for s in parts) < self._width - (len(parts) - 1) * 2:
                return ', '.join(parts)
            else:
                return ',\n  '.join(parts)


class NoAction(Action):
    def __init__(self, **kwargs):
        kwargs.setdefault('default', SUPPRESS)
        kwargs.setdefault('nargs', 0)
        super(NoAction, self).__init__(**kwargs)

    def __call__(self, parser,
                 namespace, values,
                 option_string=None):
        pass


class Documentation:
    def __init__(self, ):
        super().__init__()
        self.actions = {
            'center': "Center the focused window to a float window",
            'float': "Toggle the float of a window (overrides config file for otf movements)",
            'resize': "Resize focused window (if float)",
            'snap': "Runs grid placement (can be combined with all other actions). Arguments include rows, cols, and target.",
        }
        _rc_def = '(default in rc file)'
        _slc_txt = lambda ax: f'The number of {ax} slices in screen grid {_rc_def}'
        self.flags = {
            'rows': {'type':'int', 'help':_slc_txt('row')},
            'cols': {'type':'int', 'help':_slc_txt('col')},
            'target': {'type':'int', 'help':f'The grid location to snap the window to {_rc_def}'}
        }

    def build_parser(self,choices: list) -> ArgumentParser:
        parser = ArgumentParser(description='Manage your floating windows with ease.',formatter_class=CustomFormatter)
        parser.register('action', 'none', NoAction)
        parser.add_argument('actions', metavar='<action>', type=str, nargs='+',
                            choices=choices,
                            help=self.action_header())

        for flag in self.flags:
            parser.add_argument(f'--{flag}',
                    type=eval(self.flags[flag]['type']),
                    help=self.flags[flag]['help'])

        group = parser.add_argument_group(title='Actions')
        for action, desc in self.actions.items():
            group.add_argument(action, help=desc, action='none')
        return parser

    def action_header(self) -> str:
        return """Actions are the functions to execute on the current window.
                  Order of operations matters here. For Example:
                  "python floatwm.py center float --target 3"
                  We can assume that this command is for a tiled window (as the user passed an option to make the window float).
                  This will try to center the window to grid position 3 but fails, as it is not floating. The proper order would be:
                  "python floatwm.py float center --target 3"
                  A minimum of one action is required to run the script."""

    def action_choices(self) -> str:
        help_str = "Actions:\n"
        for action, desc in self.actions.items():
            help_str += f'{action}\t{desc}\n'

        return help_str
