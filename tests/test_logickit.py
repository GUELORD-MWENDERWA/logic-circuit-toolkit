from itertools import product

import pytest

from logickit import (
    canonical_sop, format_table, full_adder, half_adder, minimize, minterms,
    multiplexer, parse, ripple_carry_adder, sop_from_minterms,
)


def equivalent(a: str, b: str) -> bool:
    ea, eb = parse(a), parse(b)
    names = sorted(set(ea.variables()) | set(eb.variables()))
    return all(
        ea.eval(dict(zip(names, bits))) == eb.eval(dict(zip(names, bits)))
        for bits in product((0, 1), repeat=len(names))
    )


@pytest.mark.parametrize("text", ["A.B + !C", "A B' + C", "(A XOR B) AND C", "~(A | B)", "A'' + 0"])
def test_parser_accepts_common_notations(text):
    parse(text)


def test_precedence():
    assert minterms("A + B.C") == [3, 4, 5, 6, 7]
    assert minterms("A ^ B") == [1, 2]


def test_syntax_errors():
    for bad in ("A +", "(A", "A B )"):
        with pytest.raises(SyntaxError):
            parse(bad)


def test_truth_table_text():
    text = format_table("A.B")
    assert text.splitlines()[-1].endswith("| 1")


def test_minimize_classic_examples():
    assert minimize("A'B'C + A'BC + AB'C + ABC") == "C"
    assert equivalent(minimize("A.B + A.B' + A'.B"), "A + B")
    # Consensus theorem: A.B + A'.C + B.C == A.B + A'.C
    assert equivalent(minimize("A.B + A'.C + B.C"), "A.B + A'.C")
    assert minimize("A.B + A'.C + B.C").count("+") == 1


def test_minimize_with_dont_cares():
    # f = sum(1,3,5,7) + d(6): the don't-care must not be forced into the result
    names = ["A", "B", "C"]
    assert sop_from_minterms([1, 3, 5, 7], names, [6]) == "C"
    # BCD digit greater than 4 with don't-cares 10-15
    r = sop_from_minterms([5, 6, 7, 8, 9], list("ABCD"), range(10, 16))
    assert equivalent(r, "A + B.D + B.C")


def test_minimization_preserves_function_on_random_like_inputs():
    for ones in ([0, 2, 5, 7], [1, 2, 4, 7], [0, 1, 2, 3, 8, 9, 10, 11], [3, 5, 6, 7, 9, 10, 12, 13, 14, 15]):
        names = list("ABCD")
        r = sop_from_minterms(ones, names)
        assert minterms(r, names) == sorted(ones)


def test_canonical_sop():
    assert canonical_sop([1, 2], ["A", "B"]) == "A'.B + A.B'"


def test_half_and_full_adder():
    ha, fa = half_adder(), full_adder()
    for a, b in product((0, 1), repeat=2):
        assert ha.simulate({"A": a, "B": b}) == {"S": (a + b) % 2, "C": (a + b) // 2}
    for a, b, c in product((0, 1), repeat=3):
        out = fa.simulate({"A": a, "B": b, "Cin": c})
        assert out["S"] + 2 * out["Cout"] == a + b + c


def test_ripple_carry_adder_4_bits():
    rca = ripple_carry_adder(4)
    for x in range(16):
        for y in range(16):
            vals = {f"A{i}": (x >> i) & 1 for i in range(4)}
            vals |= {f"B{i}": (y >> i) & 1 for i in range(4)}
            vals["Cin"] = 0
            out = rca.simulate(vals)
            total = sum(out[f"S{i}"] << i for i in range(4)) + (out["Cout"] << 4)
            assert total == x + y


def test_multiplexer():
    mux = multiplexer()
    for s, d0, d1 in product((0, 1), repeat=3):
        assert mux.simulate({"S": s, "D0": d0, "D1": d1})["Y"] == (d1 if s else d0)
