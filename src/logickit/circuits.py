"""Gate-level combinational circuit simulator.

A Circuit is a netlist of named wires driven by gates. Gates are evaluated in
topological order, so circuits must be acyclic (combinational).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

GATES: dict[str, Callable[[list[int]], int]] = {
    "AND": lambda v: int(all(v)),
    "OR": lambda v: int(any(v)),
    "NOT": lambda v: 1 - v[0],
    "NAND": lambda v: 1 - int(all(v)),
    "NOR": lambda v: 1 - int(any(v)),
    "XOR": lambda v: sum(v) % 2,
    "XNOR": lambda v: 1 - sum(v) % 2,
    "BUF": lambda v: v[0],
}


@dataclass
class Gate:
    kind: str
    inputs: list[str]
    output: str


@dataclass
class Circuit:
    inputs: list[str]
    outputs: list[str]
    gates: list[Gate] = field(default_factory=list)

    def add(self, kind: str, inputs: list[str], output: str) -> "Circuit":
        kind = kind.upper()
        if kind not in GATES:
            raise ValueError(f"unknown gate {kind}")
        if any(g.output == output for g in self.gates) or output in self.inputs:
            raise ValueError(f"wire {output!r} already has a driver")
        self.gates.append(Gate(kind, list(inputs), output))
        return self

    def _ordered(self) -> list[Gate]:
        ready = set(self.inputs)
        pending = list(self.gates)
        order: list[Gate] = []
        while pending:
            progress = False
            for g in list(pending):
                if all(i in ready for i in g.inputs):
                    order.append(g)
                    ready.add(g.output)
                    pending.remove(g)
                    progress = True
            if not progress:
                missing = {i for g in pending for i in g.inputs if i not in ready}
                raise ValueError(f"undriven wires or combinational loop: {sorted(missing)}")
        return order

    def simulate(self, values: dict[str, int]) -> dict[str, int]:
        """Evaluate the circuit and return the value of every output."""
        wires = {k: int(bool(values[k])) for k in self.inputs}
        for g in self._ordered():
            wires[g.output] = GATES[g.kind]([wires[i] for i in g.inputs])
        return {o: wires[o] for o in self.outputs}

    def gate_count(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for g in self.gates:
            counts[g.kind] = counts.get(g.kind, 0) + 1
        return counts


def half_adder() -> Circuit:
    c = Circuit(["A", "B"], ["S", "C"])
    return c.add("XOR", ["A", "B"], "S").add("AND", ["A", "B"], "C")


def full_adder() -> Circuit:
    c = Circuit(["A", "B", "Cin"], ["S", "Cout"])
    c.add("XOR", ["A", "B"], "p").add("XOR", ["p", "Cin"], "S")
    c.add("AND", ["A", "B"], "g").add("AND", ["p", "Cin"], "t")
    return c.add("OR", ["g", "t"], "Cout")


def ripple_carry_adder(bits: int) -> Circuit:
    """n-bit adder: inputs A0..A{n-1}, B0..B{n-1}, Cin; outputs S0..S{n-1}, Cout."""
    ins = [f"A{i}" for i in range(bits)] + [f"B{i}" for i in range(bits)] + ["Cin"]
    outs = [f"S{i}" for i in range(bits)] + ["Cout"]
    c = Circuit(ins, outs)
    carry = "Cin"
    for i in range(bits):
        nxt = "Cout" if i == bits - 1 else f"c{i + 1}"
        c.add("XOR", [f"A{i}", f"B{i}"], f"p{i}").add("XOR", [f"p{i}", carry], f"S{i}")
        c.add("AND", [f"A{i}", f"B{i}"], f"g{i}").add("AND", [f"p{i}", carry], f"t{i}")
        c.add("OR", [f"g{i}", f"t{i}"], nxt)
        carry = nxt
    return c


def multiplexer() -> Circuit:
    """2-to-1 multiplexer: Y = S'.D0 + S.D1."""
    c = Circuit(["S", "D0", "D1"], ["Y"])
    c.add("NOT", ["S"], "ns").add("AND", ["ns", "D0"], "a").add("AND", ["S", "D1"], "b")
    return c.add("OR", ["a", "b"], "Y")
