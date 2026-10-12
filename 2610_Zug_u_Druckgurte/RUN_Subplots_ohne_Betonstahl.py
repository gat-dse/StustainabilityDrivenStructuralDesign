"""
Zug- und Druckgurte aller Materialien – Darstellung wie Vorlage:
  a) Zuggurt   b) Druckgurt   (getrennte Subplots)   c) Querschnitte

Variante OHNE Betonstahl (nackt): wie RUN_Subplots.py, Materialien in EXCLUDE werden weggelassen.
Berechnung, Materialien und CO2-Werte stammen aus RUN.py (Median + 10%/90%-Fraktile).
Beim Druckgurt sind Verkürzung u und Druckkraft N positiv aufgetragen.
"""

import re
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import RUN as base

mm = base.mm
HERE = Path(__file__).resolve().parent

EXCLUDE = ("s",)        # nicht dargestellte Materialien (s = Betonstahl nackt)

# 'Beton' als eigenes Wort -> 'Stahlbeton' (nicht in 'Betonstahl' oder 'Stahlbeton')
_BETON = re.compile(r"(?<![A-Za-zÄÖÜäöü])Beton(?![a-zäöü])")


def stahlbeton(text):
    return _BETON.sub("Stahlbeton", text)


# Beschriftungen je Subplot: key -> (u auf Medianlinie [mm], Textposition (u, N) [mm, MN], Krümmung)
NOTES_TENSION = {
    "t24": (0.6, (0.45, 20.5), 0.25),
    "t":   (0.9, (1.45, 22.0), 0.2),
    "a":   (2.8, (2.45, 18.0), -0.2),
    "s":   (3.3, (3.55, 18.0), 0.2),
    "rc":  (3.6, (3.45, 1.4), -0.2),
    "pc":  (2.3, (1.85, 1.75), 0.2),
}
NOTES_COMPRESSION = {
    "t24": (0.9, (0.5, 24.0), -0.2),
    "t":   (1.25, (1.8, 23.5), 0.15),
    "rc":  (2.8, (2.15, 20.3), 0.1),
    "cc":  (3.0, (3.45, 17.6), 0.2),
    "s":   (2.9, (2.95, 1.4), -0.15),
    "a":   (1.8, (2.0, 1.4), 0.15),
}


def _style_axis(ax, u_max, y_max, ylabel, title):
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


def _panel(ax, sign, notes, uu, u_max):
    """Zeichnet alle Materialien für Zug (sign=+1) oder Druck (sign=-1, positiv aufgetragen)."""
    ends = []
    for m in base.MATERIALS:
        if m["key"] in EXCLUDE:
            continue
        f, (k50, k10, k90), col = m["f"], m["keys"], m["color"]
        N50, N10, N90 = (sign * f(sign * uu, k) / 1e6 for k in (k50, k10, k90))
        if np.max(np.abs(N50)) < 1e-9:          # Material trägt in dieser Richtung nicht
            continue
        ax.fill_between(uu / mm, N10, N90, color=col, alpha=0.35, lw=0, zorder=1)
        for Nf in (N10, N90):
            ax.plot(uu / mm, base._hide_zero(uu, Nf), color=col, ls=(0, (3, 2)), lw=1.1, zorder=2)
        ax.plot(uu / mm, base._hide_zero(uu, N50), color=col, lw=2.8, zorder=4)

        u_ult = base._ultimate_u(f, k50, sign)
        if abs(u_ult) > u_max * mm:
            ends.append((float(N50[-1]), u_ult, col))

        if m["key"] in notes:
            u_t, xytext, rad = notes[m["key"]]
            y_t = np.interp(u_t, uu / mm, N50)
            label = m.get("name_t" if sign > 0 else "name_c", m["name"])
            ax.annotate(stahlbeton(label), xy=(u_t, y_t), xytext=xytext, fontsize=14,
                        ha="center", va="center", zorder=6,
                        bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.8),
                        arrowprops=dict(arrowstyle="-|>", color="k", lw=1.1, mutation_scale=14,
                                        shrinkA=4, shrinkB=1,
                                        connectionstyle=f"arc3,rad={rad}"))
    if ends:
        base._end_arrows(ax, ends, u_max, +1, min_gap=1.2)


def plot(u_max=4, n=2001, y_max=27.5, fname="last_verformung_subplots_ohne_betonstahl.png"):
    uu = np.linspace(0, u_max, n) * mm

    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.3, 1.0], hspace=0.16, wspace=0.22,
                          left=0.05, right=0.93, top=0.96, bottom=0.10)
    axt = fig.add_subplot(gs[0, 0])
    axd = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, :])

    _panel(axt, +1, NOTES_TENSION, uu, u_max)
    _panel(axd, -1, NOTES_COMPRESSION, uu, u_max)
    _style_axis(axt, u_max, y_max, "$N_{Rd}$ [MN]", "Zuggurt")
    _style_axis(axd, u_max, y_max, "$N_{Rd}^{-}$ [MN]", "Druckgurt")

    handles = [Line2D([], [], color="k", lw=2.8, label="Median $e$"),
               Line2D([], [], color="k", lw=1.1, ls=(0, (3, 2)), label="10%- / 90%-Fraktil $e$")]
    axt.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 0.93), frameon=False,
               fontsize=12.5, title="Budget: 100 kgCO$_2$ pro m Gurtlänge", title_fontsize=12.5)

    # Querschnitte aus RUN.py, Bezeichnungen 'Beton' -> 'Stahlbeton'
    _sections(axc)
    for t in axc.texts:
        t.set_text(stahlbeton(t.get_text()))

    for ax, lab, dx in ((axt, "a)", -0.07), (axd, "b)", -0.07), (axc, "c)", -0.03)):
        ax.text(dx, 1.02, lab, transform=ax.transAxes, fontsize=17, va="bottom")
    base.save_fig(fig, HERE / fname, bbox_inches="tight", pad_inches=0.2)
    return fig


def _sections(axc, exclude=EXCLUDE):
    """Querschnitte aus RUN._sections, ohne die Materialien in `exclude`."""
    base._sections(axc, exclude=exclude,
                   titles={"cc": f"Umschnürter Beton C30/37|$\\rho_w$ = {base.RHO_W:.1%}, $\\rho_l$ = {base.RHO_L:.1%}"})


if __name__ == "__main__":
    plot()
    plt.show()
