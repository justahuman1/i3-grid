# i3-grid.py

i3-grid is a module to manage floating windows for the
i3 tiling window manager. The code is split into several classes, each
isolating the logic respective to its name. The process flow is as follows:

- FloatManager: Manages the user input parsing and function dispatches

- \*Movements: Contains the functions that are directly
  called by the user to invoke window actions

- \*MonitorCalculator: Manages the xrandr display settings
  to make display agnostic window decisions

- \*FloatUtils: The meta functions of the manager that
  directly assist the movements and calculator

- Utils: Additional utilities to abstract debugging,
  RPC calls, etc.

- \*Middleware: Manages socket connections for API bindings via
  library or command line

<sup>\*Asterisk signifies meta classes that are under the hood.<sup>

We have utilized type hints and the typings library to make
the code easier to understand, as well as autocomplete for
VSCode, PyCharm, Vim, etc.

## Methods

As seen in the `__init__.py`, the classes we expose from the i3grid
module are `Documentation, FloatManager, Utils`, and `BASE_CONFIG`.
The main classes used in a library will hail from FloatManager. We will discuss
the important methods below (the remaining are intuitive or not necessary for
library usage).

You will notice that not all methods will allow an id field. This is because
of the limits of the i3-py library. I will try to patch the library to allow these
if requested but an override is to focus on a window and then act on it.

Additional comments are available in the source code.
The method descriptions are as follows:

        Class
        - method_name
                Function Header

                Description

### FloatManager

<sup>\*Asterisk signifies an abstracted command. Highly recommended for usage<sup>

- run\*

      def run(self, cmd: str, **kwargs) -> None:

      An abstraction over the raw action commands. Dispatches command, updates i3 state,
      and cleans globals/grid leaks. The available commands are as seen in the CLI help menu.
      All kwargs are passed to the specific command function (not needed most of the time).

      Commands:
            center, float, resize, snap, csize, hide, reset, listen, multi

- all_override\*

      def all_override(self, commands: list, **kwargs) -> List[tuple]:

      Used to apply functions to multiple windows. The methodology is to focus on the window
      and apply the user defined action(s). Returns the windows in the current workspace.
      The container id is available and can be activated by passing in a kwargs `id` boolean
      to True.

- update_config\*

      def update_config(self, val: dict) -> bool:

      Updates the config value used by i3-grid during the runtime. The BASE_CONFIG class will
      demonstrate how to utilize this mechanism. This will need to be called whenever you
      would like to update the configuration. This allows for you to keep multiple copies of
      BASE_CONFIG and call this function to change configurations on the fly.

- custom_resize

      def custom_resize(self, **kwargs) -> None:

      Resize the current window to custom screen percentage. The percentage is
      determined by the `DefaultResetPercentage` key in the BASE_CONFIG.

- focus_window

      def focus_window(self, **kwargs) -> None:
      Focuses on the window with given kwargs `id`

- hide_scratchpad

      def hide_scratchpad(self, **kwargs) -> None:

      Hides the scratchpad with given kwargs `id` or current window. If window
      is not assigned to a scratchpad, it will not hide it.

- make_float

      def make_float(self, **kwargs) -> None:

      Makes the current window float. If already float, do nothing.

- make_resize

      def make_resize(self, **kwargs) -> None:

      Resizes the following window into the fixed grid size (There is a seperate function
      for custom resizing) as determined by user input of Rows and Columns.

- move_to_center

      def move_to_center(self, **kwargs) -> None:

      Moves the focused window to the center of the current monitor.

- multi_select

      def multi_select(self, \*\*kwargs) -> None:

      Allows for free range select across a grid quadrants. Utilizes the
      `multis` key from BASE_CONFIG to determine the upper and lower bound.

- post_commands

      def post_commands(self) -> None:

      This function is under the hood and you will probably not need it (if you stick
      to the abstracted methods) but it is important to know. This command syncs the state
      of the workspace prior to each action to ensure data validity.

- reset_win

      def reset_win(self, **kwargs) -> None:

      Resets the window to default i3 size.

- snap_to_grid

      def snap_to_grid(self, **kwargs) -> None:

      Snaps the focused window to the grid location of choice. The location may
      be changed via the `SnapLocation` key in BASE_CONFIG. Accepts a `tc`
      kwargs for custom true center.

- start_server

      def start_server(self, data_mapper: collectionsAbc.Callable) -> None:

      Starts the live socket server for receiving other thread actions. Can be utilized as a
      data stream for bash or other message queues for daemon like features. Implemented for
      future updates.

### Utils

A majority of these functions are for the library itself and may be ignored.

- read_config

      @staticmethod
      def read_config() -> None:

      This is called when FloatManager is instantiated but may be called manually to override
      current settings.

- i3_custom

      @staticmethod
      def i3_custom(cmd: str, id: str = None) -> str:

      Constructs a command using the command string. If ID is passed it, it will customize
      the raw function to apply to the window with the given ID.

- dipatch_bash_command

      @staticmethod
      def dipatch_bash_command(command_str: str) -> str:

      Dispatch a bash command and receive the output as a string. This opens a
      bash subprocess. This can be combined with i3_custom to dispatch custom functions.

## Todos

- The CLI is seemingly far more useful as this should be a somewhat minimal library. The GitHub README contains the future features that have been inquired.
- An important TODO for the library is to allow for deep kwargs on dispatches to more specific control.
