"""
Stahlbeton-Gurte im Verlauf der Jahre (1990 - 2050)

Last-Verformungs-Verhalten N(u) eines Stahlbeton-Gurts (C30/37, L0 = 1 m) bei einem fixen
Budget von 100 kgCO2 pro m Gurtlänge, für verschiedene Betone aus dem treeze-Betonrechner
(Excel "Zementemissionen-jh.xlsx").

  Zug:  Zuggurtmodell mit Tension Stiffening (N_rc aus RUN.py)
  Druck: Beton (Sargin-Parabel, eps_c2d = 3.5 ‰) + Betonstahl

Die Materialmodelle werden aus RUN.py übernommen; hier ändern sich nur die CO2-Werte:
  e_c  [kgCO2/m3 Beton]  = "kgCO2 total" (Zeile 12) der jeweiligen Betonsorte
  e_s  [kgCO2/m3 Stahl]  = kgCO2 pro 100 kg Bewehrung (Zeilen 14/16) / 100 kg * 7850 kg/m3
                           Stahlsorte wählbar über STEEL ("Nexigen", "CH mix" oder "Gerlafingen")
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import RUN as base   # Materialmodelle, Plot-Stil und Hilfsfunktionen

mm, MPa = base.mm, base.MPa
HERE = Path(__file__).resolve().parent
XLSX = HERE / "Zementemissionen-jh.xlsx"

STEEL = "CH mix"       # Betonstahl: "Nexigen", "CH mix" (Excel Zeile 14) oder "Gerlafingen" (Zeile 16)
E_NEXIGEN = 368         # Nexigen Bewehrungsstahl [kgCO2-eq/t]
RHO_T = base.RHO_T      # Bewehrungsgehalt Zuggurt (wie RUN.py, 10 %)
RHO_C = base.RHO_C      # Bewehrungsgehalt Druckgurt (wie RUN.py, 0.6 %)
GAMMA_S = 7850          # kg/m3

# Betonsorten: (Spaltenkopf Zeile 4, Jahr in Zeile 3 oder None, Jahr für Plot, Kurzname, Farbe, Art)
# Art: "rc" = Stahlbeton (Zug + Druck), "cc" = umschnürter Stahlbeton (nur Druck, wie RUN.py)
# Die Spalten werden über den Kopf gesucht -> eingefügte Spalten im Excel stören nicht.
CONCRETES = [
    ("CEM I", 1990, 1990, "CEM I (fossil)",           "#5b3a29", "rc"),   # dunkelbraun
    ("CEM I", 2026, 2026, "CEM I (CH mix)",           "#c8a27a", "rc"),   # hellbraun
    ("NPK C CEMIIB", None, 2026, "KBOB CEM II/B",     "#d35400", "rc"),   # dunkelorange
    ("NPK C CEMIIB", None, 2026, "KBOB CEM II/B umschnürt", "#f5a04a", "cc"),  # hellorange
    ("ND Kibeco", None, 2026, "ND Kibeco (Reco200)",  "#2e9e44", "rc"),   # grün
    ("Beton 2050", None, 2050, "Beton 2050",          "#1a3c8c", "rc"),   # dunkelblau
    ("Beton 2050 mit CCUS", None, 2050, "Beton 2050 mit CCUS", "#6baed6", "rc"),  # hellblau
]


def _find_column(ws, header, year=None):
    """Spalte mit Kopf `header` (Zeile 4) und ggf. Jahr `year` (Zeile 3)."""
    for c in range(3, ws.max_column + 1):
        h = ws.cell(row=4, column=c).value
        y = ws.cell(row=3, column=c).value
        if h is not None and str(h).strip() == header and (year is None or y == year):
            return c
    raise ValueError(f"Spalte '{header}' ({year}) im Excel nicht gefunden.")


# =============================================================================
# 1) CO2-Werte aus dem Excel
# =============================================================================
def read_emissions(path=XLSX):
    """Liest e_c (Zeile 12) sowie die Stahlwerte (Zeilen 14/16) aus dem Excel.
    Excel speichert berechnete Formelwerte; die Datei muss einmal in Excel gespeichert sein."""
    import openpyxl
    from openpyxl.utils import get_column_letter
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = []
    for header, xl_year, year, name, color, kind in CONCRETES:
        c = _find_column(ws, header, xl_year)
        e_c = ws.cell(row=12, column=c).value
        col = get_column_letter(c)
        if e_c is None:
            raise ValueError(f"Zelle {col}12 leer – Excel einmal speichern (Formelwerte fehlen).")
        rows.append(dict(col=col, year=year, name=name, color=color, e_c=float(e_c), kind=kind))
    c0 = _find_column(ws, "CEM I", 1990)
    steel = {"Gerlafingen": ws.cell(row=16, column=c0).value,               # kgCO2 / 100 kg
             "CH mix": ws.cell(row=14, column=c0).value}
    e_s = {k: v / 100 * GAMMA_S for k, v in steel.items()}                # kgCO2 / m3 Stahl
    e_s["Nexigen"] = E_NEXIGEN / 1000 * GAMMA_S                           # 368 kg/t -> 2'889 kg/m3
    return rows, e_s


def N_rc_e(u, e_c, e_s, kind="rc"):
    """Gurt N(u) [N] für die CO2-Werte e_c (Beton) und e_s (Stahl).
    kind="rc": Stahlbeton (Zug RHO_T, Druck RHO_C); kind="cc": umschnürter Stahlbeton
    (nur Druck, RHO_W / RHO_L wie RUN.py)."""
    if kind == "cc":
        return base.N_cc(u, base.RHO_W, base.RHO_L, e_c, e_s)
    return base.N_rc_tc(u, e_c, e_s)


def label(r, short=False):
    """Legendentext einer Betonsorte."""
    if short:
        return f"{r['year']}: {r['name']}"
    if r["kind"] == "cc":
        return (f"{r['year']}: {r['name']}  ($\\rho_w$ = {base.RHO_W:.1%}, "
                f"$\\rho_l$ = {base.RHO_L:.1%})")
    return f"{r['year']}: {r['name']}  ($e_c$ = {r['e_c']:.0f} kgCO$_2$/m$^3$)"


# =============================================================================
# 2) Plot N(u) + Querschnitte
# =============================================================================
def plot(rows, e_s, u_min=-4, u_max=4, n=4001, fname="stahlbeton_jahre.png", dark=False,
         y_top=15.0, compact=False, slide=False, FS=16):
    """compact=True: ohne (a)/(b), Querschnitte rechts neben dem Diagramm untereinander.
    slide=True: wie compact, aber im Folienformat 16:9 mit einheitlicher, grosser Schrift
    (Grundgrösse FS [pt])."""
    if slide:
        compact = True
    # Schriftgrössen [pt]
    F = (dict(tick=FS - 1, axis=FS + 2, box=FS + 2, legend=FS - 1, text=FS - 1, end=FS - 1)
         if slide else dict(tick=13, axis=17, box=18, legend=12.5, text=13, end=14))
    uu = np.linspace(u_min, u_max, n) * mm
    es = e_s[STEEL]

    if slide:
        fig = plt.figure(figsize=(16, 9))
        ax = fig.add_axes([0.045, 0.04, 0.535, 0.92])
        axc = None
    elif compact:
        fig = plt.figure(figsize=(21, 12))
        ax = fig.add_axes([0.05, 0.04, 0.63, 0.92])
        axc = None
    else:
        fig = plt.figure(figsize=(15, 13))
        gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.12,
                              left=0.08, right=0.90, top=0.97, bottom=0.10)
        ax = fig.add_subplot(gs[0])
        axc = fig.add_subplot(gs[1])

    tens, comp = [], []
    for r in rows:
        col = r["color"]
        e_c, kind = r["e_c"], r["kind"]
        N = N_rc_e(uu, e_c, es, kind) / 1e6
        ax.plot(uu / mm, base._hide_zero(uu, N), color=col, lw=2.8, zorder=4, label=label(r, short=slide))
        for sign, store, x_edge in ((+1, tens, u_max), (-1, comp, u_min)):
            u_ult = base._ultimate_u(lambda u, k: N_rc_e(u, e_c, es, kind), None, sign)
            if abs(u_ult) > abs(x_edge) * mm:
                store.append((float(N_rc_e(x_edge * mm, e_c, es, kind) / 1e6), u_ult, col))
    if tens:
        base._end_arrows(ax, tens, u_max, +1, min_gap=1.1 if slide else 0.9, fontsize=F["end"])
    if comp:
        base._end_arrows(ax, comp, u_min, -1, min_gap=1.1 if slide else 0.9, fontsize=F["end"])

    # Achsen im Ursprung
    Nall = [l.get_ydata() for l in ax.lines]
    ymax = np.nanmax([np.nanmax(y) for y in Nall]) * 1.15
    ymin = np.nanmin([np.nanmin(y) for y in Nall]) * 1.15
    if y_top is not None:                      # Zugbereich nur bis y_top [MN]
        ymax = y_top + 0.6                     # etwas Luft für die Pfeilspitze über 10 MN
    ax.set_xlim(u_min - 0.1, u_max + 0.3)
    ax.set_ylim(ymin, ymax)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_position(("data", 0))
    ax.spines["bottom"].set_position(("data", 0))
    ax.plot(1, 0, ">k", ms=11, transform=ax.get_yaxis_transform(), clip_on=False)
    ax.plot(0, 1, "^k", ms=11, transform=ax.get_xaxis_transform(), clip_on=False)
    ax.set_xticks(np.arange(u_min, u_max + 0.01, 0.5))
    yt = 5.0 if slide else 2.5
    ax.set_yticks(np.arange(np.ceil(ymin / yt) * yt, ymax + 0.01, yt))
    ax.xaxis.set_major_formatter(lambda x, p: "" if abs(x) < 1e-9 else f"{x:.1f}")
    ax.yaxis.set_major_formatter(lambda y, p: "" if abs(y) < 1e-9 else f"{y:g}")
    ax.tick_params(direction="in", length=5, labelsize=F["tick"])
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_bbox(dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.5))
    ax.text(0.15, ymax, "$N_{Rd}$ [MN]", fontsize=F["axis"], ha="left", va="top")
    ax.text(u_max + 0.35, -0.03 * (ymax - ymin), "$u$ [mm]", fontsize=F["axis"], ha="left", va="top",
            clip_on=False)
    box = dict(boxstyle="square,pad=0.3", fc="white", ec="k", lw=1.2)
    ax.text(1.6 if not slide else 2.0, ymax * 0.97, "Zuggurt", fontsize=F["box"], ha="center",
            va="top", bbox=box)
    ax.text(-2.6, ymin * 0.97, "Druckgurt", fontsize=F["box"], ha="center", va="bottom", bbox=box)

    sep = "\n" if slide else " "
    leg1 = ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.02), frameon=False,
                     fontsize=F["legend"],
                     title=f"Stahlbeton C30/37,{sep}$\\rho_s$ = {RHO_T:.0%} (Zug), {RHO_C:.1%} (Druck)",
                     title_fontsize=F["legend"] + 1)
    leg1._legend_box.align = "left"
    ax.add_artist(leg1)
    ax.text(u_min, 0.92 * ymax, f"Betonstahl {STEEL}: $e_s$ = {base._fmt(es)} kgCO$_2$/m$^3$\n"
            "Budget: 100 kgCO$_2$ pro m Gurtlänge"
            + ("\n$e_c$ in kgCO$_2$/m$^3$" if slide else ""),
            ha="left", va="top", fontsize=F["text"], linespacing=1.5)

    if slide:
        _sections_column(fig, rows, es, x_fig=0.665, top_fig=0.97, scale_in=1.2,
                         text_in=0.82, gap_in=0.13, fontsize=FS - 1, short=True)
    elif compact:
        _sections_column(fig, rows, es)
    else:
        _sections(axc, rows, es)
        ax.text(-0.06, 1.0, "(a)", transform=ax.transAxes, fontsize=17, va="top")
        axc.text(-0.06, 1.0, "(b)", transform=axc.transAxes, fontsize=17, va="top")
    if dark:
        base.invert_bw(fig)
    base.save_fig(fig, HERE / fname, bbox_inches="tight", pad_inches=0.2)
    return fig


def _sections_column(fig, rows, e_s, x_fig=0.72, top_fig=0.96, scale_in=1.9,
                     text_in=0.95, gap_in=0.15, fontsize=12.5, short=False):
    """Querschnitte untereinander, linke Kanten bündig, Text rechts daneben.
    scale_in = Zoll pro 1000 mm (gleicher Massstab für alle Querschnitte)."""
    gk_c, gk_s = base.gamma["c"] * base.g / 1000, base.gamma["s"] * base.g / 1000
    g_rc = lambda A, r: A * ((1 - r) * gk_c + r * gk_s)
    mm_per_in = 1000.0 / scale_in
    info = []
    for r in rows:
        if r["kind"] == "cc":
            A = base.A_cc(base.RHO_W, base.RHO_L, r["e_c"], e_s)
            sq = [(np.sqrt(A) / mm, 0.85)]
            lines = [f"Druck: $\\rho_w$ = {base.RHO_W:.1%}, $\\rho_l$ = {base.RHO_L:.1%}",
                     f"   $A$ = {base._fmt(A * 1e6)} mm$^2$, "
                     f"$g_{{0k}}$ = {A * (gk_c + (base.RHO_W + base.RHO_L) * gk_s):.1f} kN/m"]
        else:
            A_t = base.A_rc(RHO_T, r["e_c"], e_s)
            A_c = base.A_rc(RHO_C, r["e_c"], e_s)
            sq = [(np.sqrt(A_c) / mm, 0.40), (np.sqrt(A_t) / mm, 0.85)]
            lines = [f"Zug ($\\rho_s$ = {RHO_T:.0%}): $A$ = {base._fmt(A_t * 1e6)} mm$^2$, "
                     f"$g_{{0k}}$ = {g_rc(A_t, RHO_T):.1f} kN/m",
                     f"Druck ($\\rho_s$ = {RHO_C:.1%}): $A$ = {base._fmt(A_c * 1e6)} mm$^2$, "
                     f"$g_{{0k}}$ = {g_rc(A_c, RHO_C):.1f} kN/m"]
        title = f"$\\bf{{{r['year']}}}$: {r['name']}  ($e_c$ = {r['e_c']:.0f} kgCO$_2$/m$^3$)"
        if short:                                    # kompakter Text fürs Folienformat
            title = (f"$\\bf{{{r['year']}}}$: {r['name']}, $e_c$ = {r['e_c']:.0f}"
                     + (f", $\\rho_w$ = {base.RHO_W:.1%}" if r["kind"] == "cc" else ""))
            if r["kind"] == "cc":
                lines = [f"Druck: $A$ = {base._fmt(A * 1e6)} mm$^2$, "
                         f"$g_{{0k}}$ = {A * (gk_c + (base.RHO_W + base.RHO_L) * gk_s):.1f} kN/m"]
            else:
                lines = [f"Zug: $A$ = {base._fmt(A_t * 1e6)} mm$^2$, $g_{{0k}}$ = {g_rc(A_t, RHO_T):.1f} kN/m",
                         f"Druck: $A$ = {base._fmt(A_c * 1e6)} mm$^2$, $g_{{0k}}$ = {g_rc(A_c, RHO_C):.1f} kN/m"]
        info.append((r, sq, [title] + lines))
    a_max = max(a for _, sq, _ in info for a, _ in sq)
    text_mm, gap_mm = text_in * mm_per_in, gap_in * mm_per_in
    heights = [max(max(a for a, _ in sq), text_mm) for _, sq, _ in info]
    H = sum(heights) + gap_mm * (len(info) - 1)
    Wmm = a_max + 0.15 * mm_per_in + (3.4 if short else 3.6) * mm_per_in   # Quadrat + Abstand + Text
    fw, fh = fig.get_size_inches()
    axc = fig.add_axes([x_fig, top_fig - H / mm_per_in / fh, Wmm / mm_per_in / fw, H / mm_per_in / fh])
    y = H
    x_text = a_max + 0.15 * mm_per_in
    for (r, sq, lines), h in zip(info, heights):
        y_top = y
        for a, alpha in sq:                                   # linke Kante bündig bei x = 0
            axc.add_patch(Rectangle((0, y_top - a), a, a, color=r["color"], alpha=alpha, lw=0))
        axc.text(x_text, y_top, "\n".join(lines), ha="left", va="top", fontsize=fontsize,
                 linespacing=1.35)
        y -= h + gap_mm
    axc.set_xlim(0, Wmm)
    axc.set_ylim(0, H)
    axc.set_aspect("equal", anchor="NW")
    axc.axis("off")
    return axc


def _sections(axc, rows, e_s):
    """Querschnitte massstäblich: hell = Druckgurt (RHO_C), dunkel = Zuggurt (RHO_T)."""
    gk_c, gk_s = base.gamma["c"] * base.g / 1000, base.gamma["s"] * base.g / 1000
    g_rc = lambda A, r: A * ((1 - r) * gk_c + r * gk_s)
    W = 1150.0
    for i, r in enumerate(rows):
        x0 = i * W
        if r["kind"] == "cc":                       # umschnürter Stahlbeton (nur Druck)
            A = base.A_cc(base.RHO_W, base.RHO_L, r["e_c"], e_s)
            a = np.sqrt(A) / mm
            axc.add_patch(Rectangle((x0, 0), a, a, color=r["color"], alpha=0.85, lw=0))
            txt = ["$\\bf{" + str(r["year"]) + "}$", r["name"].replace(" umschnürt", "\numschnürt"),
                   f"$e_c$ = {r['e_c']:.0f} kgCO$_2$/m$^3$",
                   f"Druck: $\\rho_w$ = {base.RHO_W:.1%},",
                   f"   $\\rho_l$ = {base.RHO_L:.1%}",
                   f"   $A$ = {base._fmt(A * 1e6)} mm$^2$",
                   f"   $g_{{0k}}$ = {A * (gk_c + (base.RHO_W + base.RHO_L) * gk_s):.1f} kN/m"]
            axc.annotate("\n".join(txt), xy=(x0, 0), xytext=(0, -10), textcoords="offset points",
                         ha="left", va="top", fontsize=12, linespacing=1.5, annotation_clip=False)
            continue
        A_t = base.A_rc(RHO_T, r["e_c"], e_s)
        A_c = base.A_rc(RHO_C, r["e_c"], e_s)
        a_t, a_c = np.sqrt(A_t) / mm, np.sqrt(A_c) / mm
        axc.add_patch(Rectangle((x0, 0), a_c, a_c, color=r["color"], alpha=0.40, lw=0))
        axc.add_patch(Rectangle((x0, 0), a_t, a_t, color=r["color"], alpha=0.85, lw=0))
        txt = ["$\\bf{" + str(r["year"]) + "}$", r["name"],
               f"$e_c$ = {r['e_c']:.0f} kgCO$_2$/m$^3$",
               f"Zug: $\\rho_s$ = {RHO_T:.0%}",
               f"   $A$ = {base._fmt(A_t * 1e6)} mm$^2$",
               f"   $g_{{0k}}$ = {g_rc(A_t, RHO_T):.1f} kN/m",
               f"Druck: $\\rho_s$ = {RHO_C:.1%}",
               f"   $A$ = {base._fmt(A_c * 1e6)} mm$^2$",
               f"   $g_{{0k}}$ = {g_rc(A_c, RHO_C):.1f} kN/m"]
        axc.annotate("\n".join(txt), xy=(x0, 0), xytext=(0, -10), textcoords="offset points",
                     ha="left", va="top", fontsize=12, linespacing=1.5, annotation_clip=False)
    axc.set_xlim(-30, max(len(rows), 5) * W)
    axc.set_ylim(0, 800)
    axc.set_aspect("equal", anchor="NW")
    axc.axis("off")

# =============================================================================
# 3) Tabelle
# =============================================================================
def table(rows, e_s):
    out = []
    for r in rows:
        line = {"Jahr": r["year"], "Beton": r["name"], "e_c [kgCO2/m3]": r["e_c"]}
        es = e_s[STEEL]
        if r["kind"] == "cc":
            A_t = np.nan
            A_c = base.A_cc(base.RHO_W, base.RHO_L, r["e_c"], es)
            uu = np.linspace(-40, 60, 8000) * mm
        else:
            A_t = base.A_rc(RHO_T, r["e_c"], es)
            A_c = base.A_rc(RHO_C, r["e_c"], es)
            uu = np.linspace(-3.5, 60, 6000) * mm
        N = N_rc_e(uu, r["e_c"], es, r["kind"]) / 1e6
        line[f"A Zug (rho={RHO_T:.1%}) [mm²]"] = A_t * 1e6
        line[f"a Zug [mm]"] = np.sqrt(A_t) / mm
        line[f"A Druck (rho={RHO_C:.1%}) [mm²]"] = A_c * 1e6
        line[f"a Druck [mm]"] = np.sqrt(A_c) / mm
        line["N_Zug,max [MN]"] = N.max() if r["kind"] != "cc" else np.nan
        line["N_Druck,max [MN]"] = -N.min()
        out.append(line)
    import pandas as pd
    return pd.DataFrame(out).set_index(["Jahr", "Beton"])


if __name__ == "__main__":
    rows, e_s = read_emissions()
    tab = table(rows, e_s)
    import pandas as pd
    with pd.option_context("display.float_format", "{:,.1f}".format, "display.width", 250,
                           "display.max_columns", None):
        print(tab)
    tab.to_csv(HERE / "stahlbeton_jahre.csv", float_format="%.2f")
    plot(rows, e_s)
    plot(rows, e_s, fname="stahlbeton_jahre_dark.png", dark=True)   # schwarz/weiss invertiert
    plot(rows, e_s, fname="stahlbeton_jahre_kompakt.png", compact=True)  # Querschnitte rechts
    plot(rows, e_s, fname="stahlbeton_jahre_kompakt_dark.png", compact=True, dark=True)
    plot(rows, e_s, fname="stahlbeton_jahre_folie.png", slide=True)            # Folie 16:9
    plot(rows, e_s, fname="stahlbeton_jahre_folie_dark.png", slide=True, dark=True)
    plt.show()
