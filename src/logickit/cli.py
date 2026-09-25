"""Command-line interface.

    logickit table "A.B + C'"
    logickit minimize "A'B'C + A'BC + AB'C + ABC"
    logickit minterms 3 1,3,5,7 --dc 6
"""

from __future__ import annotations

import argparse

from . import canonical_pos, canonical_sop, format_table, minimize, minterms, parse, sop_from_minterms


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="logickit", description="Boolean algebra toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("table", help="print the truth table of an expression")
    t.add_argument("expr")

    m = sub.add_parser("minimize", help="minimise an expression to a sum of products")
    m.add_argument("expr")

    mt = sub.add_parser("minterms", help="minimise from a minterm list")
    mt.add_argument("n_vars", type=int)
    mt.add_argument("ones", help="comma-separated minterms, e.g. 1,3,5")
    mt.add_argument("--dc", default="", help="comma-separated don't-care terms")

    args = ap.parse_args(argv)
    if args.cmd == "table":
        print(format_table(args.expr))
    elif args.cmd == "minimize":
        e = parse(args.expr)
        names = e.variables()
        ones = minterms(e, names)
        print(f"variables : {', '.join(names)}")
        print(f"minterms  : {ones}")
        print(f"canonical : {canonical_sop(ones, names)}")
        print(f"POS       : {canonical_pos(ones, names)}")
        print(f"minimal   : {minimize(e)}")
    else:
        names = [chr(ord("A") + i) for i in range(args.n_vars)]
        ones = [int(x) for x in args.ones.split(",") if x]
        dcs = [int(x) for x in args.dc.split(",") if x]
        print(sop_from_minterms(ones, names, dcs))


if __name__ == "__main__":
    main()
