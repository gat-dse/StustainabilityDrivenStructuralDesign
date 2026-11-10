"""
Zug- und Druckgurte mit fixem KOSTEN-Budget von 100 CHF pro m Gurtlänge
  a) Zuggurt   b) Druckgurt   (getrennte Subplots)   c) Querschnitte

Gleiche Materialmodelle und gleiche Darstellung wie RUN_Subplots.py, aber statt der
CO2-Werte e [kgCO2/m3] werden Kosten k [CHF/m3] eingesetzt:
    A = 100 CHF / (k * 1 m)
Mittelwert (ausgezogen) und Min/Max-Werte (gestrichelt, Band) der Kosten.
Beim Druckgurt sind Verkürzung u und Druckkraft N positiv aufgetragen.
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import RUN as base
import RUN_Subplots as sub          # Achsenstil, 'Beton' -> 'Stahlbeton'

mm = base.mm
HERE = Path(__file__).resolve().parent

# =============================================================================
# Kostenannahmen: (Bezeichnung, Mittelwert CHF/m3, Streuung +/-, CHF/t nur zur Angabe im Plot)
# =============================================================================
COSTS = {
    #  key    Bezeichnung im Plot                        CHF/m3   +/-   CHF/t
    "c":   ("Beton (inkl. Schalung)",                       400, 0.25, 160),
    "s":   ("Betonstahl",                                 12000, 0.40, 1500),
    "p":   ("Spannstahl",                                 48000, 0.50, 6000),
    "a":   ("Baustahl (inkl. Korrosionsschutz)",          32000, 0.50, 4000),
    "t":   ("BSH GL24h (inkl. Montage + Verbinder)",       2000, 0.25, 4000),
    "t24": ("Vollholz C24 (inkl. Montage + Verbinder)",   1600, 0.25, 3200),
}
# Vollholz: Annahme ca. 80 % von BSH (Materialpreise Handel CH), nicht im Plot angegeben


def cost_values():
    """Kosten im Format von RUN.e: key = Mittelwert, key+'10' = Min, key+'90' = Max."""
    k = dict(base.e)                         # übrige Schlüssel (nicht geplottet) unverändert
    for key, (_, mean, dev, _) in COSTS.items():
        k[key] = mean
        k[key + "10"] = mean * (1 - dev)     # Min-Kosten -> grösserer Querschnitt
        k[key + "90"] = mean * (1 + dev)     # Max-Kosten -> kleinerer Querschnitt
    return k


# Kostenzeilen je Querschnitt in c): key -> [(Kürzel, Kosten-Key), ...], Zusatzzeilen
SECTION_COSTS = {
    "pc":  ([("c", "c"), ("p", "p")], ["Betonkosten inkl. Schalung"]),
    "a":   ([("", "a")], ["inkl. Korrosionsschutz"]),
    "s":   ([("", "s")], []),
    "rc":  ([("c", "c"), ("s", "s")], ["Betonkosten inkl. Schalung"]),
    "cc":  ([("c", "c"), ("s", "s")], ["Betonkosten inkl. Schalung"]),
    "t":   ([("", "t")], ["inkl. Montage + Verbinder"]),
    "t24": ([("", "t24")], ["inkl. Montage + Verbinder"]),
}
SECTION_ORDER = ["pc", "a", "s", "rc", "cc", "t", "t24"]      # Reihenfolge wie RUN._sections


def cost_lines(key, short=False):
    """Kostenzeilen für den Querschnitt `key`, z.B. '$k_c$ = 400 CHF/m$^3$, ±25%' + '(160 CHF/t)'.
    short=True (Folie): ohne CHF/t und ohne Zusatzzeilen (stehen dort in der Legende)."""
    parts, extra = SECTION_COSTS[key]
    out = []
    for sym, ck in parts:
        _, mean, dev, per_t = COSTS[ck]
        k = "$k$" if not sym else f"$k_{sym}$"
        out.append(f"{k} = {base._fmt(mean)} CHF/m$^3$, $\\pm${dev:.0%}")
        if not short:
            out.append(f"     ({base._fmt(per_t)} CHF/t)")
    return out if short else out + extra


def cost_table():
    """Text für die Box mit den Kostenannahmen."""
    lines = []
    for key, (name, mean, dev, per_t) in COSTS.items():
        lines.append(f"{name}: {base._fmt(mean)} CHF/m$^3$ ({base._fmt(per_t)} CHF/t), "
                     f"$\\pm${dev:.0%}")
    return "\n".join(lines)


# Beschriftungen je Subplot: key -> (u auf Mittelwertlinie [mm], Textposition (u, N) [mm, MN], Krümmung)
NOTES_TENSION = {
    "t24": (0.5, (0.3, 3.0), 0.2),
    "t":   (0.8, (1.0, 3.4), 0.2),
    "a":   (2.6, (2.6, 3.0), -0.2),
    "s":   (3.3, (3.55, 5.0), 0.2),
    "rc":  (3.6, (2.6, 5.2), -0.2),
    "pc":  (2.3, (1.0, 5.0), 0.2),
}
NOTES_COMPRESSION = {
    "t24": (0.9, (0.45, 4.0), -0.2),
    "t":   (1.2, (1.4, 2.6), 0.15),
    "rc":  (2.8, (2.2, 8.8), 0.1),
    "cc":  (3.0, (3.45, 9.0), 0.2),
    "s":   (2.9, (3.3, 3.2), -0.15),
    "a":   (1.8, (2.45, 2.4), 0.15),
}


def _panel(ax, sign, notes, uu, u_max, exclude):
    """Alle Materialien für Zug (sign=+1) oder Druck (sign=-1, positiv aufgetragen)."""
    ends, n_max = [], 0.0
    for m in base.MATERIALS:
        if m["key"] in exclude:
            continue
        f, (k50, k10, k90), col = m["f"], m["keys"], m["color"]
        N50, N10, N90 = (sign * f(sign * uu, k) / 1e6 for k in (k50, k10, k90))
        if np.max(np.abs(N50)) < 1e-9:          # Material trägt in dieser Richtung nicht
            continue
        n_max = max(n_max, np.max(N10), np.max(N90))
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
            ax.annotate(sub.stahlbeton(label), xy=(u_t, y_t), xytext=xytext, fontsize=14,
                        ha="center", va="center", zorder=6,
                        bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.8),
                        arrowprops=dict(arrowstyle="-|>", color="k", lw=1.1, mutation_scale=14,
                                        shrinkA=4, shrinkB=1,
                                        connectionstyle=f"arc3,rad={rad}"))
    if ends:
        base._end_arrows(ax, ends, u_max, +1, min_gap=0.45)
    return n_max


def _set_rho_t(rho_t):
    """Bewehrungsgehalt Stahlbeton-Zuggurt setzen (wirkt auf Kurven, Beschriftung, Querschnitte)."""
    base.RHO_T = rho_t
    for m in base.MATERIALS:
        if m["key"] == "rc":
            m["name_t"] = f"Stahlbeton\nC30/37, $\\rho_s$={rho_t:.0%}"
            m["name"] = f"Stahlbeton C30/37\n$\\rho_s$={rho_t:.0%} (Zug), {base.RHO_C:.1%} (Druck)"


def plot(exclude=(), rho_t=None, u_max=4, n=2001, y_max=11.0, fname="kosten_subplots.png",
         dark=False, slide=False):
    """exclude: nicht dargestellte Materialien (z.B. ("s",) = ohne Betonstahl nackt).
    rho_t: Bewehrungsgehalt Zuggurt (None = Wert aus RUN.py).
    dark=True: schwarz/weiss invertiert; slide=True: Folienformat 16:9 (Zug und Druck in einem
    Diagramm, Querschnitte rechts)."""
    rho_old = base.RHO_T
    if rho_t is not None:
        _set_rho_t(rho_t)
    try:
        with base.emissions(cost_values()):
            if slide:
                fig = _plot_slide(exclude, u_max, 2 * n)
            else:
                fig = _plot(exclude, u_max, n, y_max)
        if dark:
            base.invert_bw(fig)
        base.save_fig(fig, HERE / fname, bbox_inches="tight", pad_inches=0.2)
        return fig
    finally:
        _set_rho_t(rho_old)


def _plot(exclude, u_max, n, y_max):
    uu = np.linspace(0, u_max, n) * mm

    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.3, 1.0], hspace=0.16, wspace=0.22,
                          left=0.05, right=0.93, top=0.96, bottom=0.10)
    axt = fig.add_subplot(gs[0, 0])
    axd = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, :])

    nt = _panel(axt, +1, NOTES_TENSION, uu, u_max, exclude)
    nd = _panel(axd, -1, NOTES_COMPRESSION, uu, u_max, exclude)
    sub._style_axis(axt, u_max, y_max, "$N_{Rd}$ [MN]", "Zuggurt")
    sub._style_axis(axd, u_max, y_max, "$N_{Rd}^{-}$ [MN]", "Druckgurt")
    axt.set_yticks(np.arange(0, y_max, 1.0))
    axd.set_yticks(np.arange(0, y_max, 1.0))

    # Legende + Kostenannahmen in einer punktierten Box (Zuggurt, oben rechts)
    handles = [Line2D([], [], color="k", lw=2.8, label="Mittelwert Kosten"),
               Line2D([], [], color="k", lw=1.1, ls=(0, (3, 2)), label="Min / Max Kosten")]
    title = ("Budget: 100 CHF pro Gurtlänge\n"
             "$k$: Kosten, Mittelwert und Min/Max (siehe c)")
    leg = axt.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.07, 0.92),
                     frameon=True, fancybox=False, fontsize=12.5, title_fontsize=12.5,
                     title=title, borderpad=0.7, handlelength=2.6)
    leg._legend_box.align = "left"
    leg.get_title().set_linespacing(1.45)
    _dotted(leg.get_frame())
    leg.set_zorder(10)

    # Querschnitte aus RUN.py, Bezeichnungen 'Beton' -> 'Stahlbeton'
    base._sections(axc, exclude=exclude, titles=CC_TITLE(),
                   extra={k: cost_lines(k) for k in SECTION_COSTS})
    for t in axc.texts:
        t.set_text(sub.stahlbeton(t.get_text()))

    for ax, lab, dx in ((axt, "a)", -0.07), (axd, "b)", -0.07), (axc, "c)", -0.03)):
        ax.text(dx, 1.02, lab, transform=ax.transAxes, fontsize=17, va="bottom")
    return fig


def CC_TITLE():
    return {"cc": f"Umschnürter Beton|C30/37, $\\rho_w$ = {base.RHO_W:.1%}, "
                  f"$\\rho_l$ = {base.RHO_L:.1%}"}


# =============================================================================
# Folienformat 16:9: Zug (oben) und Druck (unten) in einem Diagramm, Querschnitte rechts
# =============================================================================
FS = 16                                              # Grundschriftgrösse Folie [pt]
SLIDE_YLIM = (-10.0, 8.5)
SLIDE_LAYOUT = [["rc", "cc"], ["pc", "a"], ["s"], ["t", "t24"]]
# key -> Liste von (u auf Mittelwertlinie [mm], Textposition (u, N), Krümmung); u < 0: Druck
SLIDE_LABELS = {
    "rc":  [(3.6, (3.3, 4.6), -0.2), (-0.9, (1.9, -5.0), -0.2)],
    "cc":  [(-1.6, (1.9, -7.4), -0.25)],
    "s":   [(2.6, (0.8, 4.7), -0.2)],
    "a":   [(3.0, (3.2, -1.2), 0.15)],
    "pc":  [(2.3, (1.5, 6.9), -0.25)],
    "t":   [(0.9, (1.5, -2.9), -0.25)],
    "t24": [(0.55, (0.6, -1.45), -0.2)],
}


def notes_text():
    """Hinweise zu den Kostenansätzen (Folie, in der Legende)."""
    return ("$k$: Kosten, Mittelwert und Min/Max\n"
            "Beton inkl. Schalung, Baustahl inkl. Korrosionsschutz,\n"
            "Holz inkl. Montage + Verbinder")


def _plot_slide(exclude, u_max, n):
    u_min = -u_max
    ylim = SLIDE_YLIM
    uu = np.linspace(u_min, u_max, n) * mm
    F = dict(label=FS, tick=FS - 1, axis=FS + 2, box=FS + 2, legend=FS - 2, end=FS - 2)

    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_axes([0.045, 0.03, 0.545, 0.94])
    axc = fig.add_axes([0.645, 0.015, 0.355, 0.97])

    tens, comp = [], []
    for m in base.MATERIALS:
        if m["key"] in exclude:
            continue
        f, (k50, k10, k90), col = m["f"], m["keys"], m["color"]
        N50, N10, N90 = (f(uu, k) / 1e6 for k in (k50, k10, k90))
        ax.fill_between(uu / mm, N10, N90, color=col, alpha=0.35, lw=0, zorder=1)
        for Nf in (N10, N90):
            ax.plot(uu / mm, base._hide_zero(uu, Nf), color=col, ls=(0, (3, 2)), lw=1.1, zorder=2)
        ax.plot(uu / mm, base._hide_zero(uu, N50), color=col, lw=2.8, zorder=4)
        for sign, store, x_edge in ((+1, tens, u_max), (-1, comp, u_min)):
            u_ult = base._ultimate_u(f, k50, sign)
            if abs(u_ult) > abs(x_edge) * mm:
                store.append((float(f(x_edge * mm, k50) / 1e6), u_ult, col))
        for u_t, xytext, rad in SLIDE_LABELS.get(m["key"], []):
            y_t = np.interp(u_t, uu / mm, N50)
            label = m.get("name_c" if u_t < 0 else "name_t", m["name"])
            ax.annotate(sub.stahlbeton(label), xy=(u_t, y_t), xytext=xytext, fontsize=F["label"],
                        ha="center", va="center", color=col, zorder=6,
                        bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.75),
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.3, mutation_scale=14,
                                        shrinkA=4, shrinkB=1, connectionstyle=f"arc3,rad={rad}"))
    gap = 0.045 * (ylim[1] - ylim[0])
    if tens:
        base._end_arrows(ax, tens, u_max, +1, min_gap=gap, fontsize=F["end"])
    if comp:
        base._end_arrows(ax, comp, u_min, -1, min_gap=gap, fontsize=F["end"])

    # Achsen im Ursprung
    ax.set_xlim(u_min - 0.1, u_max + 0.3)
    ax.set_ylim(*ylim)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.spines["left"].set_position(("data", 0))
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["left"].set_zorder(5)
    ax.plot(1, 0, ">k", ms=11, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", ms=11, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_xticks(np.arange(u_min, u_max + 0.01, 1.0))
    ax.set_yticks(np.arange(np.ceil(ylim[0] / 2.5) * 2.5, ylim[1], 2.5))
    ax.xaxis.set_major_formatter(lambda x, p: "" if abs(x) < 1e-9 else f"{x:.0f}")
    ax.yaxis.set_major_formatter(lambda y, p: "" if abs(y) < 1e-9 else f"{y:g}")
    ax.tick_params(direction="in", length=5, labelsize=F["tick"])
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_bbox(dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.5))
    ax.text(0.15, ylim[1], "$N_{Rd}$ [MN]", fontsize=F["axis"], ha="left", va="top")
    ax.text(u_max + 0.35, -0.3, "$u$ [mm]", fontsize=F["axis"], ha="left", va="top", clip_on=False)
    box = dict(boxstyle="square,pad=0.3", fc="white", ec="k", lw=1.2)
    ax.text(3.2, ylim[1] - 0.2, "Zuggurt", fontsize=F["box"], ha="center", va="top", bbox=box)
    ax.text(-2.5, ylim[0] + 0.2, "Druckgurt", fontsize=F["box"], ha="center", va="bottom", bbox=box)

    # Legende + Hinweise oben links (Quadrant u < 0, N > 0)
    handles = [Line2D([], [], color="k", lw=2.8, label="Mittelwert Kosten"),
               Line2D([], [], color="k", lw=1.1, ls=(0, (3, 2)), label="Min / Max Kosten")]
    leg = ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 1.0),
                    frameon=True, fancybox=False, fontsize=F["legend"], title_fontsize=F["legend"],
                    title="Budget: 100 CHF pro Gurtlänge", borderpad=0.6, handlelength=2.4)
    leg._legend_box.align = "left"
    _dotted(leg.get_frame())
    leg.set_zorder(10)
    ax.text(-4.05, 4.15, notes_text(), fontsize=F["legend"] - 1, ha="left", va="top",
            linespacing=1.35, zorder=10)

    # Querschnitte rechts (2 Spalten), Kosten je Querschnitt
    layout = [r for r in SLIDE_LAYOUT if any(k not in exclude for k in r)]
    base._sections(axc, exclude=exclude, layout=layout, W=2000.0,
                   fontsize=FS - 2, linespacing=1.15, line_mm=158.0, titles=CC_TITLE(),
                   extra={k: cost_lines(k, short=True) for k in SECTION_COSTS})
    for t in axc.texts:
        t.set_text(sub.stahlbeton(t.get_text()))
    axc.set_anchor("NW")
    return fig


def _dotted(frame):
    frame.set_linestyle((0, (1, 2)))
    frame.set_edgecolor("k")
    frame.set_linewidth(1.2)
    frame.set_facecolor("white")
    frame.set_alpha(1.0)


if __name__ == "__main__":
    # alle Materialien, rho_s Zug = 10 % (RUN.py)
    plot()
    plot(fname="kosten_subplots_dark.png", dark=True)
    plot(fname="kosten_folie.png", slide=True)
    plot(fname="kosten_folie_dark.png", slide=True, dark=True)
    # ohne Betonstahl (nackt), rho_s Zug = 8 %
    kw = dict(exclude=("s",), rho_t=0.08)
    plot(fname="kosten_subplots_ohne_betonstahl.png", **kw)
    plot(fname="kosten_subplots_ohne_betonstahl_dark.png", dark=True, **kw)
    plot(fname="kosten_folie_ohne_betonstahl.png", slide=True, **kw)
    plot(fname="kosten_folie_ohne_betonstahl_dark.png", slide=True, dark=True, **kw)
    plt.show()
