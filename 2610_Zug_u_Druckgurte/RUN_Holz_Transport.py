"""
Balkendiagramm: CO2-Werte ohne Transport, mit Bahntransport und mit LKW-Transport für Holz
(Konstruktionsvollholz KVH C24, Brettschichtholz GL24h) und Stahl (Betonstahl B500B, Baustahl S355).
Werte aus dem Excel "261008_Mathcad Werte.xlsx", Blatt "Werte fib Betontag", Zeilen [kgCO2/m3]:
    ohne Transport: E (Median), F (90%), G (10%)
    Bahn:           K (Median), L (90%), M (10%)
    LKW:            H (Median), I (90%), J (10%)
Balken = Median, Fehlerbalken = 10%- / 90%-Fraktil.
Holz und Stahl unterscheiden sich um rund Faktor 50 -> zwei Teildiagramme mit eigener y-Skala.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

import RUN as base

HERE = Path(__file__).resolve().parent
XLSX = HERE / "261008_Mathcad Werte.xlsx"
SHEET = "Werte fib Betontag"

GROUPS = [                                   # (Titel, [(key, Bezeichnung), ...])
    ("Holz",  [("t24", "Konstruktionsvollholz\nKVH C24"), ("t", "Brettschichtholz\nGL24h")]),
    ("Stahl", [("s", "Betonstahl\nB500B"), ("a", "Baustahl\nS355")]),
]
# Zeile im Excel: Text in Spalte A (Anfang) + Einheit [kgCO2/m3] in Spalte C
ROWS = {"t24": "C24 nur Vollholz", "t": "BSH GL24h", "s": "Bewehrungsstahl B500B", "a": "Baustahl"}
# (Text, Spalten Median/10%/90%, Deckkraft)
CASES = [("ohne\nTransport", ("E", "G", "F"), 0.4),
         ("Bahn",             ("K", "M", "L"), 0.7),
         ("LKW",              ("H", "J", "I"), 1.0)]


def read_values(path=XLSX):
    """{key: [(Median, 10%, 90%) je Fall in CASES]} aus dem Excel (Formelwerte)."""
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True)[SHEET]
    out = {}
    for key, name in ROWS.items():
        row = next((r for r in range(1, ws.max_row + 1)
                    if str(ws[f"A{r}"].value or "").startswith(name)
                    and ws[f"C{r}"].value == "[kgCO2/m3]"), None)
        if row is None:
            print(f"Zeile '{name}' nicht im Excel -> Ersatzwerte FALLBACK['{key}']")
            out[key] = FALLBACK[key]
            continue
        out[key] = [tuple(float(ws[f"{c}{row}"].value) for c in cols) for _, cols, _ in CASES]
    return out


# Ersatzwerte, falls die Zeile im Excel (noch) fehlt: (Median, 10%, 90%) für ohne / Bahn / LKW
FALLBACK = {
    "t24": [(55.0, 53.0, 74.0), (74.0, 67.0, 81.0), (181.0, 130.0, 227.0)],   # C24 nur Vollholz
}


def _fmt(v):
    return base._fmt(v)


def _panel(ax, items, vals):
    x = np.arange(len(items))
    w = 0.27
    top = max(hi for k, _ in items for _, _, hi in vals[k])
    for j, (text, _, alpha) in enumerate(CASES):
        for i, (k, _) in enumerate(items):
            col = next(m["color"] for m in base.MATERIALS if m["key"] == k)
            med, lo, hi = vals[k][j]
            xi = x[i] + (j - 1) * w
            ax.bar(xi, med, w * 0.92, color=col, alpha=alpha, edgecolor=col, lw=1.2, zorder=3)
            ax.errorbar(xi, med, yerr=[[med - lo], [hi - med]], fmt="none", ecolor="k",
                        elinewidth=1.2, capsize=5, zorder=4)
            # Median direkt auf die Oberkante des Balkens (verdeckt den Fehlerbalken dort)
            ax.text(xi, med, _fmt(med), ha="center", va="center", fontsize=12.5, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, lw=1.2))
            ax.text(xi, 0.015 * top, text, ha="center", va="bottom", fontsize=11, zorder=5)
    ax.set_xticks(x)
    ax.set_xticklabels([n for _, n in items], fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.yaxis.set_major_formatter(lambda y, p: _fmt(y))
    ax.set_ylim(0, 1.08 * top)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.grid(axis="y", alpha=0.3, zorder=0)


def plot(fname="holz_transport_balken.png", dark=False, vals=None):
    vals = read_values() if vals is None else vals
    fig, axs = plt.subplots(1, 2, figsize=(15, 6.5))
    for ax, (title, items) in zip(axs, GROUPS):
        _panel(ax, items, vals)
        ax.set_title(title, fontsize=17)
    axs[0].set_ylabel("$e$ [kgCO$_2$/m$^3$]", fontsize=15)
    fig.text(0.99, 0.01, "Balken und Zahl: Median, Fehlerbalken: 10%- / 90%-Fraktil "
             "(unterschiedliche y-Skalen Holz / Stahl)", ha="right", va="bottom", fontsize=12)
    fig.tight_layout(rect=(0, 0.04, 1, 1), w_pad=3)
    if dark:
        base.invert_bw(fig)
    base.save_fig(fig, HERE / fname, bbox_inches="tight", pad_inches=0.2)
    return fig


if __name__ == "__main__":
    plot()
    plot(fname="holz_transport_balken_dark.png", dark=True)
    plt.show()
