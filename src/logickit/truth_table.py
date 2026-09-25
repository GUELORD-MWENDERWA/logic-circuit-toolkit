"""Truth tables and minterm extraction."""

from __future__ import annotations

from itertools import product

from .expr import Expr, parse


def _as_expr(e: Expr | str) -> Expr:
    return parse(e) if isinstance(e, str) else e


def truth_table(e: Expr | str, variables: list[str] | None = None) -> tuple[list[str], list[tuple[tuple[int, ...], int]]]:
    """Return (variables, rows) where each row is (inputs, output).

    Rows are in binary counting order, the first variable being the most significant bit.
    """
    e = _as_expr(e)
    names = variables or e.variables()
    rows = []
    for bits in product((0, 1), repeat=len(names)):
        rows.append((bits, int(e.eval(dict(zip(names, bits))))))
    return names, rows


def minterms(e: Expr | str, variables: list[str] | None = None) -> list[int]:
    """Indices of the rows where the expression is true."""
    names, rows = truth_table(e, variables)
    return [i for i, (_, out) in enumerate(rows) if out]


def format_table(e: Expr | str, variables: list[str] | None = None) -> str:
    """Render a truth table as aligned plain text."""
    e = _as_expr(e)
    names, rows = truth_table(e, variables)
    header = " ".join(names) + " | F"
    lines = [header, "-" * len(header)]
    for bits, out in rows:
        cells = " ".join(str(b).rjust(len(n)) for b, n in zip(bits, names))
        lines.append(f"{cells} | {out}")
    return "\n".join(lines)
