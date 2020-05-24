import sys
import datetime
import logging
from i3grid import Documentation, FloatManager, Utils

# Logger for stdout
logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s |%(lineno)d]: %(message)s')
logger = logging.getLogger(__name__)


def _debugger() -> None:
    """Evaluates user input expression."""
    logger.info("Entering debug mode. Evaluating input:")
    while 1:
        cmd = input(">>> ")
        logger.info(eval(cmd))


def _sole_commands(args):
    if "listen" in args.actions:
        assert (
            len(args.actions)
        ) == 1, "'Listen' is a sole command. Do not pass additional actions"
        # Utils.read_config()
        # Utils.on_the_fly_override(port=args.port)
        listener = FloatManager(check=False)
        try:
            listener.start_server(data_mapper=print)
        except KeyboardInterrupt:
            print()  # New line
            logger.info("Closing i3-grid socket...")
        finally:
            exit(0)


if __name__ == "__main__":
    if "debug" in sys.argv:
        _debugger()
        exit(0)

    start = datetime.datetime.now()
    try:
        doc = Documentation()
    except NameError:
        logger.critical("Missing Documentation (doc.py). Exiting..")
        exit(1)

    comx = list(doc.actions)
    parser = doc.build_parser(choices=comx)
    args = parser.parse_args()
    # Check for sole commands (Static for now, only 1 value)
    _sole_commands(args)
    manager = FloatManager(commands=comx, **args.__dict__,)
    for action in args.actions:
        manager.run(cmd=action)

    end = datetime.datetime.now()
    logger.info(f"Total Time: {end - start}")
    exit(0)
