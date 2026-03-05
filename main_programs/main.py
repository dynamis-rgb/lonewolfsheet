import sys

from modules.Cli import CliApp
from modules.JsonRepository import JsonRepository


def main() -> int:
    App = CliApp(Repo=JsonRepository())
    return App.Run(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())