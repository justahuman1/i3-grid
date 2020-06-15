import sys
import datetime
import logging
try:
    from i3grid import Documentation, FloatManager, Utils
except ModuleNotFoundError:
    # Github custom download
    from doc import Documentation
    from grid import FloatManager, Utils

# Logger for stdout
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s %(levelname)s |%(lineno)d]: %(message)s"
)
logger = logging.getLogger(__name__)


def _debugger() -> None:
    """Evaluates user input expression."""
    logger.info("Entering debug mode. Evaluating input:")
    m = FloatManager(check=False)
    print(">>> m = FloatManager(check=False)  # m.run(<cmd>)")
    while 1:
        start = datetime.datetime.now()
        cmd = input(">>> ")
        logger.info(eval(cmd))
        end = datetime.datetime.now()
        logger.info(f"Total Time: {end - start}")


def _sole_commands(args):
    if "listen" in args.actions:
        assert (
            len(args.actions)
        ) == 1, "'Listen' is a sole command. Do not pass additional actions"
        listener = FloatManager(check=False)
        try:
            listener.start_server(data_mapper=print)
        except KeyboardInterrupt:
            print()
            logger.info("Closing i3-grid socket...")
        finally:
            exit(0)


if __name__ == "__main__":
    if "debug" in sys.argv:
        _debugger()
        exit(0)
    try:
        doc = Documentation()
    except NameError:
        logger.critical("Missing Documentation (doc.py). Exiting..")
        exit(1)
    comx = list(Documentation.actions)
    parser = doc.build_parser(choices=comx)
    args = parser.parse_args()
    # Check for sole commands (Static for now, only 1 value)
    _sole_commands(args)
    manager = FloatManager(commands=comx, **args.__dict__,)
    if not manager._TERMSIG:
        for action in args.actions:
            manager.run(cmd=action)
    exit(0)
