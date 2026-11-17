"""CLI dispatcher for tools.corpus subcommands."""

from __future__ import annotations

import argparse
from typing import Sequence

from tools.corpus.harvest_web_ir import main as harvest_web_ir_main


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch `python -m tools.corpus <command>` invocations."""

    parser = argparse.ArgumentParser(prog="python -m tools.corpus")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "harvest-web-ir",
        add_help=False,
        help="Harvest aligned copy units from Web manual.ir.json files.",
    )
    known, rest = parser.parse_known_args(list(argv) if argv is not None else None)
    if known.command == "harvest-web-ir":
        return harvest_web_ir_main(rest)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
