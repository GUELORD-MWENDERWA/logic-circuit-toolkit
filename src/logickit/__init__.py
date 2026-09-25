"""logickit: Boolean algebra and digital logic toolkit."""

from .expr import Expr, parse
from .truth_table import truth_table, minterms, format_table
from .minimize import minimize, prime_implicants, sop_from_minterms, canonical_sop, canonical_pos
from .circuits import Circuit, half_adder, full_adder, ripple_carry_adder, multiplexer

__all__ = [
    "Expr", "parse",
    "truth_table", "minterms", "format_table",
    "minimize", "prime_implicants", "sop_from_minterms", "canonical_sop", "canonical_pos",
    "Circuit", "half_adder", "full_adder", "ripple_carry_adder", "multiplexer",
]
__version__ = "0.1.0"
