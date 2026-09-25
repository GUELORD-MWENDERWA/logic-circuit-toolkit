"""Regenerate the figures in docs/images from the library itself.

    pip install -e . matplotlib
    python docs/make_figures.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from logickit import full_adder

OUT = Path(__file__).resolve().parent / "images"
plt.rcParams.update({"figure.dpi": 150})


def full_adder_timing() -> None:
    fa = full_adder()
    signals = ["A", "B", "Cin", "S", "Cout"]
    rows = []
    for n in range(8):
        a, b, cin = n >> 2 & 1, n >> 1 & 1, n & 1
        out = fa.simulate({"A": a, "B": b, "Cin": cin})
        rows.append({"A": a, "B": b, "Cin": cin, "S": out["S"], "Cout": out["Cout"]})
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for k, name in enumerate(signals):
        y0 = (len(signals) - 1 - k) * 1.5
        values = [r[name] for r in rows] + [rows[-1][name]]
        ax.step(range(9), [y0 + v for v in values], where="post", lw=2, color="tab:blue" if k < 3 else "tab:red")
        ax.text(-0.3, y0 + 0.4, name, ha="right", va="center", weight="bold")
    for n in range(8):
        ax.axvline(n, color="gray", lw=0.5, ls=":")
        ax.text(n + 0.5, -0.8, format(n, "03b"), ha="center", fontsize=8, family="monospace")
    ax.set(xlim=(-1, 8.2), ylim=(-1.1, 7.2), title="Full adder simulated gate by gate: inputs (blue), outputs (red)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "full_adder_timing.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    full_adder_timing()
