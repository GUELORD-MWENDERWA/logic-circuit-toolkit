"""Two-level logic minimisation with the Quine-McCluskey method.

Implicants are represented as strings over {'0', '1', '-'}, one character per
variable, most significant variable first (e.g. '1-0' covers 100 and 110).
"""

from __future__ import annotations

from itertools import combinations, product
from typing import Iterable


def _bits(m: int, n: int) -> str:
    return format(m, f"0{n}b")


def _combine(a: str, b: str) -> str | None:
    diff = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if len(diff) != 1 or "-" in (a[diff[0]], b[diff[0]]):
        return None
    i = diff[0]
    return a[:i] + "-" + a[i + 1 :]


def _covers(implicant: str, m: int) -> bool:
    return all(c == "-" or c == b for c, b in zip(implicant, _bits(m, len(implicant))))


def prime_implicants(ones: Iterable[int], n_vars: int, dont_cares: Iterable[int] = ()) -> set[str]:
    """All prime implicants of the function defined by minterms and don't-cares."""
    current = {_bits(m, n_vars) for m in set(ones) | set(dont_cares)}
    primes: set[str] = set()
    while current:
        used: set[str] = set()
        nxt: set[str] = set()
        for a, b in combinations(sorted(current), 2):
            c = _combine(a, b)
            if c is not None:
                nxt.add(c)
                used.update((a, b))
        primes |= current - used
        current = nxt
    return primes


def _select_cover(primes: set[str], ones: list[int]) -> list[str]:
    """Essential prime implicants first, then Petrick's method for the rest."""
    remaining = set(ones)
    chosen: list[str] = []

    # Essential primes: the only implicant covering some minterm.
    for m in ones:
        covering = [p for p in primes if _covers(p, m)]
        if len(covering) == 1 and covering[0] not in chosen:
            chosen.append(covering[0])
    for p in chosen:
        remaining -= {m for m in remaining if _covers(p, m)}
    if not remaining:
        return sorted(chosen)

    # Petrick's method on the remaining minterms: choose the smallest,
    # then cheapest (fewest literals), set of primes that covers them.
    candidates = sorted(p for p in primes if p not in chosen and any(_covers(p, m) for m in remaining))
    options = [[p for p in candidates if _covers(p, m)] for m in sorted(remaining)]
    best: tuple[int, int, tuple[str, ...]] | None = None
    for combo in product(*options):
        s = tuple(sorted(set(combo)))
        cost = (len(s), sum(len(p) - p.count("-") for p in s), s)
        if best is None or cost < best:
            best = cost
    return sorted(chosen + list(best[2]))


def _term(implicant: str, names: list[str]) -> str:
    lits = [n if c == "1" else n + "'" for c, n in zip(implicant, names) if c != "-"]
    return ".".join(lits) if lits else "1"


def sop_from_minterms(ones: Iterable[int], names: list[str], dont_cares: Iterable[int] = ()) -> str:
    """Minimal sum-of-products expression for the given minterms."""
    ones = sorted(set(ones))
    if not ones:
        return "0"
    n = len(names)
    primes = prime_implicants(ones, n, dont_cares)
    cover = _select_cover(primes, ones)
    return " + ".join(_term(p, names) for p in cover)


def minimize(expr, dont_cares: Iterable[int] = ()) -> str:
    """Minimise a Boolean expression (string or Expr) to a sum of products."""
    from .truth_table import _as_expr, minterms

    e = _as_expr(expr)
    names = e.variables()
    return sop_from_minterms(minterms(e, names), names, dont_cares)


def canonical_sop(ones: Iterable[int], names: list[str]) -> str:
    """Canonical sum of minterms, e.g. A'.B.C + A.B'.C'."""
    n = len(names)
    return " + ".join(_term(_bits(m, n), names) for m in sorted(set(ones))) or "0"


def canonical_pos(ones: Iterable[int], names: list[str]) -> str:
    """Canonical product of maxterms."""
    n = len(names)
    ones = set(ones)
    zeros = [m for m in range(2**n) if m not in ones]
    if not zeros:
        return "1"
    clauses = []
    for m in zeros:
        lits = [nm + "'" if b == "1" else nm for b, nm in zip(_bits(m, n), names)]
        clauses.append("(" + " + ".join(lits) + ")")
    return ".".join(clauses)
