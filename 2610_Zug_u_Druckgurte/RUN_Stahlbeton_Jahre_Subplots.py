"""
Stahlbeton-Gurte im Verlauf der Jahre (1990 - 2050) – Darstellung wie Vorlage:
  a) Zuggurt   b) Druckgurt   (getrennte Subplots)   c) Querschnitte

Daten (Excel) und Berechnung werden aus RUN_Stahlbeton_Jahre.py bzw. RUN.py übernommen.
Beim Druckgurt sind Verkürzung u und Druckkraft N positiv aufgetragen.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import RUN as base
import RUN_Stahlbeton_Jahre as jahre

mm = base.mm
HERE = Path(__file__).resolve().parent
STEEL = jahre.STEEL
RHO_T = jahre.RHO_T
RHO_C = jahre.RHO_C


def rename(rows):
    """'Beton ...' -> 'Stahlbeton ...' in den Bezeichnungen."""
    for r in rows:
        r["name"] = r["name"].replace("Beton", "Stahlbeton")
    return rows


def _style_axis(ax, u_max, y_max, ylabel, title):
    """Achsen im Ursprung mit Pfeilspitzen, Stil wie Vorlage."""
    ax.set_xlim(0, u_max + 0.3)
    ax.set_ylim(0, y_max)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.plot(1, 0, ">k", ms=11, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", ms=11, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_xticks(np.arange(0, u_max + 0.01, 0.5))
    ax.set_yticks(np.arange(0, y_max, 2.5))
    ax.xaxis.set_major_formatter(lambda x, p: "0" if abs(x) < 1e-9 else f"{x:.1f}")
    ax.yaxis.set_major_formatter(lambda y, p: "0" if abs(y) < 1e-9 else f"{y:g}")
    ax.tick_params(direction="in", length=5, labelsize=13)
    ax.text(0.03 * u_max, y_max, ylabel, fontsize=17, ha="left", va="top")
    ax.text(u_max + 0.42, 0.0, "$u$ [mm]", fontsize=17, ha="left", va="center", clip_on=False)
    box = dict(boxstyle="square,pad=0.3", fc="white", ec="k", lw=1.2)
    ax.text(0.5, 1.0, title, transform=ax.transAxes, fontsize=18, ha="center", va="top", bbox=box)


def plot(rows, e_s, u_max=4, n=2001, fname="stahlbeton_jahre_subplots.png", dark=False):
    uu = np.linspace(0, u_max, n) * mm
    es = e_s[STEEL]

    fig = plt.figure(figsize=(17, 12.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1.0], hspace=0.18, wspace=0.22,
                          left=0.06, right=0.93, top=0.96, bottom=0.08)
    axt = fig.add_subplot(gs[0, 0])
    axd = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, :])

    curves = []
    for r in rows:
        Nt = jahre.N_rc_e(uu, r["e_c"], es, r["kind"]) / 1e6        # Zug
        Nd = -jahre.N_rc_e(-uu, r["e_c"], es, r["kind"]) / 1e6      # Druck (positiv)
        curves.append((r, Nt, Nd))

    y_max = 1.15 * max(max(np.max(Nt), np.max(Nd)) for _, Nt, Nd in curves)
    y_max = np.ceil(y_max / 2.5) * 2.5

    handles = {}
    for ax, sign, idx in ((axt, +1, 1), (axd, -1, 2)):
        ends = []
        for c in curves:
            r, N = c[0], c[idx]
            if np.max(np.abs(N)) < 1e-9:                         # trägt in dieser Richtung nicht
                continue
            ln, = ax.plot(uu / mm, base._hide_zero(uu, N), color=r["color"], lw=2.8, zorder=4,
                          label=jahre.label(r))
            handles.setdefault(r["name"], ln)
            e_c, kind = r["e_c"], r["kind"]
            u_ult = base._ultimate_u(lambda u, k: jahre.N_rc_e(u, e_c, es, kind), None, sign)
            if abs(u_ult) > u_max * mm:
                ends.append((float(N[-1]), u_ult, r["color"]))
        if ends:
            base._end_arrows(ax, ends, u_max, +1, min_gap=0.9)

    _style_axis(axt, u_max, y_max, "$N_{Rd}$ [MN]", f"Zuggurt, $\\rho_s$ = {RHO_T:.0%}")
    _style_axis(axd, u_max, y_max, "$N_{Rd}^{-}$ [MN]", f"Druckgurt, $\\rho_s$ = {RHO_C:.1%}")

    leg = axt.legend(handles=[handles[r["name"]] for r in rows if r["name"] in handles],
                     loc="upper left", bbox_to_anchor=(0.06, 0.93), frameon=False, fontsize=12,
                     title="Stahlbeton C30/37", title_fontsize=13)
    leg._legend_box.align = "left"
    axt.text(0.08, 0.52, f"Betonstahl {STEEL}: $e_s$ = {base._fmt(es)} kgCO$_2$/m$^3$\n"
             "Budget: 100 kgCO$_2$ pro m Gurtlänge", transform=axt.transAxes,
             ha="left", va="top", fontsize=12.5, linespacing=1.6)

    _sections(axc, rows, es)
    for ax, lab in ((axt, "a)"), (axd, "b)"), (axc, "c)")):
        ax.text(-0.07 if ax is not axc else -0.03, 1.02, lab, transform=ax.transAxes,
                fontsize=17, va="bottom")
    if dark:
        base.invert_bw(fig)
    base.save_fig(fig, HERE / fname, bbox_inches="tight", pad_inches=0.2)
    return fig


def _sections(axc, rows, e_s):
    """Querschnitte wie RUN_Stahlbeton_Jahre (hell = Druck, dunkel = Zug)."""
    jahre._sections(axc, rows, e_s)


if __name__ == "__main__":
    rows, e_s = jahre.read_emissions()
    rows = rename(rows)
    tab = jahre.table(rows, e_s)
    import pandas as pd
    with pd.option_context("display.float_format", "{:,.1f}".format, "display.width", 250,
                           "display.max_columns", None):
        print(tab)
    plot(rows, e_s)
    plot(rows, e_s, fname="stahlbeton_jahre_subplots_dark.png", dark=True)   # invertiert
    plt.show()
