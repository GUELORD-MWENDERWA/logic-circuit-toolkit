"""Boolean expression parser and evaluator.

Grammar (lowest to highest precedence):

    expr    := xor ( ('+' | '|' | 'OR') xor )*
    xor     := term ( ('^' | 'XOR') term )*
    term    := factor ( ('.' | '*' | '&' | 'AND' | <juxtaposition>) factor )*
    factor  := ('!' | '~' | 'NOT') factor | primary "'"*
    primary := VAR | '0' | '1' | '(' expr ')'

A variable is one letter optionally followed by digits (A, B, x1, D10), so
textbook juxtaposition works: "AB'C" means A AND NOT B AND C.

Examples: "A.B + !C", "AB' + C", "(A XOR B) AND C".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

_TOKEN = re.compile(r"\s*(?:(AND|OR|XOR|NOT)\b|([A-Za-z][0-9]*)|([01])|(.))")


@dataclass(frozen=True)
class Expr:
    op: str                     # 'var', 'const', 'not', 'and', 'or', 'xor'
    args: tuple = ()
    name: str | None = None
    value: bool | None = None

    def eval(self, env: Mapping[str, bool | int]) -> bool:
        if self.op == "var":
            if self.name not in env:
                raise KeyError(f"no value for variable {self.name!r}")
            return bool(env[self.name])
        if self.op == "const":
            return bool(self.value)
        vals = [a.eval(env) for a in self.args]
        if self.op == "not":
            return not vals[0]
        if self.op == "and":
            return all(vals)
        if self.op == "or":
            return any(vals)
        if self.op == "xor":
            return sum(vals) % 2 == 1
        raise ValueError(f"unknown operator {self.op}")

    def variables(self) -> list[str]:
        """Variable names, sorted alphabetically so truth tables are stable."""
        found: set[str] = set()

        def walk(e: Expr) -> None:
            if e.op == "var":
                found.add(e.name)
            for a in e.args:
                walk(a)

        walk(self)
        return sorted(found)

    def __str__(self) -> str:
        if self.op == "var":
            return self.name
        if self.op == "const":
            return "1" if self.value else "0"
        if self.op == "not":
            inner = str(self.args[0])
            return f"{inner}'" if self.args[0].op in ("var", "const") else f"({inner})'"
        sep = {"and": ".", "or": " + ", "xor": " ^ "}[self.op]
        parts = []
        for a in self.args:
            s = str(a)
            if a.op in ("or", "xor") and a.op != self.op:
                s = f"({s})"
            parts.append(s)
        return sep.join(parts)


class _Parser:
    def __init__(self, text: str):
        self.tokens: list[tuple[str, str]] = []
        for kw, var, const, other in _TOKEN.findall(text):
            if kw:
                self.tokens.append(("kw", kw))
            elif var:
                self.tokens.append(("var", var))
            elif const:
                self.tokens.append(("const", const))
            elif other.strip():
                self.tokens.append(("sym", other))
        self.pos = 0

    def peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> tuple[str, str]:
        tok = self.peek()
        if tok is None:
            raise SyntaxError("unexpected end of expression")
        self.pos += 1
        return tok

    def parse(self) -> Expr:
        e = self.expr()
        if self.peek() is not None:
            raise SyntaxError(f"unexpected token {self.peek()[1]!r}")
        return e

    def expr(self) -> Expr:
        items = [self.xor()]
        while self.peek() in (("sym", "+"), ("sym", "|"), ("kw", "OR")):
            self.take()
            items.append(self.xor())
        return items[0] if len(items) == 1 else Expr("or", tuple(items))

    def xor(self) -> Expr:
        items = [self.term()]
        while self.peek() in (("sym", "^"), ("kw", "XOR")):
            self.take()
            items.append(self.term())
        return items[0] if len(items) == 1 else Expr("xor", tuple(items))

    def _starts_factor(self) -> bool:
        tok = self.peek()
        return tok is not None and (
            tok[0] in ("var", "const") or tok in (("sym", "("), ("sym", "!"), ("sym", "~"), ("kw", "NOT"))
        )

    def term(self) -> Expr:
        items = [self.factor()]
        while True:
            tok = self.peek()
            if tok in (("sym", "."), ("sym", "*"), ("sym", "&"), ("kw", "AND")):
                self.take()
                items.append(self.factor())
            elif self._starts_factor():
                items.append(self.factor())
            else:
                break
        return items[0] if len(items) == 1 else Expr("and", tuple(items))

    def factor(self) -> Expr:
        if self.peek() in (("sym", "!"), ("sym", "~"), ("kw", "NOT")):
            self.take()
            return Expr("not", (self.factor(),))
        e = self.primary()
        while self.peek() == ("sym", "'"):
            self.take()
            e = Expr("not", (e,))
        return e

    def primary(self) -> Expr:
        kind, val = self.take()
        if kind == "var":
            return Expr("var", name=val)
        if kind == "const":
            return Expr("const", value=val == "1")
        if (kind, val) == ("sym", "("):
            e = self.expr()
            if self.take() != ("sym", ")"):
                raise SyntaxError("missing closing parenthesis")
            return e
        raise SyntaxError(f"unexpected token {val!r}")


def parse(text: str) -> Expr:
    """Parse a Boolean expression into an Expr tree."""
    return _Parser(text).parse()
