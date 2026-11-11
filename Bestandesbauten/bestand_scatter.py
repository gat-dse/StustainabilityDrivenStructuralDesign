# -*- coding: utf-8 -*-
"""
Scatterplot nur der Bestandesbauten, ohne die Kurven des Deckenrechners.

x-Achse: massgebende Spannweite [m]
y-Achse: a) GWP der tragenden Schichten, b) GWP total inklusive Bodenaufbau

Eingang: <Zeitstempel>_Bestandesanalyse_Wohnbauten.xlsx aus bestand_auswertung.py
Ausgang: Diagramme/<Zeitstempel>_Bestand_Scatter.(png|pdf)

Objekte ohne Spannweite oder ohne GWP-Wert erscheinen nicht im Diagramm; sie sind im Blatt
"Offene Punkte" des Excels aufgefuehrt.
"""

import glob
import os
from datetime import date

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

HIER = os.path.dirname(os.path.abspath(__file__))
DIAGRAMME = os.path.join(HIER, "Diagramme")

# Versatz der Beschriftung je Objekt [Punkte], wenn der automatische Wechsel nicht reicht.
# Schluessel: der Objektname gilt fuer beide Teilbilder, ("a", Name) bzw. ("b", Name) nur fuer eines.
VERSATZ_OBJEKT = {
    "Regina Kaegi Hof": (18, -28),
    "Sihlfeld": (-18, 22),
    "Ruggaechern H21": (18, -22),
    "Toblerstrasse": (-18, 22),
    "Glattpark": (18, -55),
}

VARIANTE = "EPD heute"      # "EPD heute" oder "KBOB": welche Betonannahme den Punkt setzt
BEIDE_VARIANTEN = True      # True: die jeweils andere Annahme als Strich dazu, zeigt die Bandbreite
BESCHRIFTEN = True

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 13, "axes.labelsize": 13, "axes.titlesize": 13,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 11,
    "figure.dpi": 110, "savefig.dpi": 300,
})

# Darstellung nach Deckentyp
STIL = {
    "Stahlbeton-Flachdecke":   dict(marker="s", color="#1f4e79", label="Stahlbeton-Flachdecke"),
    "Stahlbeton-Vollplatte":   dict(marker="s", color="#1f4e79", label="Stahlbeton-Flachdecke"),
    "Holzbalkendecke mit":     dict(marker="D", color="#4f7a28", label="Holzbalkendecke mit Überbeton"),
    "Holzbalkendecke":         dict(marker="D", color="#8c6d31", label="Holzbalkendecke"),
    "Holz-Beton-Verbunddecke": dict(marker="P", color="#7f3f98", label="Holz-Beton-Verbunddecke"),
    "Hourdisdecke":            dict(marker="X", color="#777777", label="Hourdisdecke"),
}

SPALTEN = {
    "EPD heute": ("GWP tragend, EPD heute [kg CO₂-eq/m²]", "GWP total, EPD heute [kg CO₂-eq/m²]"),
    "KBOB":      ("GWP tragend, KBOB [kg CO₂-eq/m²]", "GWP total, KBOB [kg CO₂-eq/m²]"),
}


def neuestes_excel():
    # Sperrdateien von geoeffneten Excel-Arbeitsmappen ("~$...") ueberspringen
    treffer = sorted((p for p in glob.glob(os.path.join(HIER, "*_Bestandesanalyse_Wohnbauten.xlsx"))
                      if not os.path.basename(p).startswith("~$")), key=os.path.getmtime)
    if not treffer:
        raise FileNotFoundError("Bestandesanalyse-Excel nicht gefunden. Zuerst bestand_auswertung.py laufen lassen.")
    return treffer[-1]


def stil_fuer(deckentyp):
    for schluessel in sorted(STIL, key=len, reverse=True):
        if str(deckentyp).startswith(schluessel):
            return STIL[schluessel]
    return dict(marker="o", color="#333333", label="übrige")


def zeichne(ax, df, spalte_haupt, spalte_zweit, achsentitel, titel, teilbild=""):
    ax.set_xlim(3, 7)
    gesehen, eintraege = set(), []
    # Beschriftungen gestaffelt setzen: Punkte mit aehnlicher Lage bekommen unterschiedliche
    # vertikale Versaetze, damit sich die Namen nicht ueberdecken
    # Beschriftung abgesetzt, mit duenner Verbindungslinie zum Punkt. Aufeinanderfolgende
    # Punkte (nach x und y sortiert) werden abwechselnd nach oben und unten gesetzt, damit
    # nahe beieinander liegende Objekte lesbar bleiben.
    versatz = [(18, 15), (-18, -15), (18, -15), (-18, 15)]
    i = 0
    df = df.sort_values(["massgebende Spannweite [m]", spalte_haupt], na_position="last")
    for _, z in df.iterrows():
        y = z.get(spalte_haupt)
        if pd.isna(z.get("massgebende Spannweite [m]")) or pd.isna(y):
            continue
        x = z["massgebende Spannweite [m]"]
        s = stil_fuer(z["Deckentyp"])
        belegt = z["Data Validation"] >= 2
        y2 = z.get(spalte_zweit)
        if BEIDE_VARIANTEN and not pd.isna(y2):
            ax.plot([x, x], [y, y2], color=s["color"], linewidth=1.0, alpha=0.45, zorder=2)
            ax.plot([x], [y2], marker="_", markersize=9, color=s["color"], alpha=0.7, zorder=2)
        ax.scatter(x, y, marker=s["marker"], s=90, zorder=4,
                   facecolors=s["color"] if belegt else "white",
                   edgecolors=s["color"], linewidths=1.7)
        if BESCHRIFTEN:
            name = str(z["Objekt"]).split(",")[0]
            eigen = VERSATZ_OBJEKT.get((teilbild, name), VERSATZ_OBJEKT.get(name))
            if eigen is not None:
                dx, dy = eigen
            else:
                dx, dy = versatz[i % len(versatz)]
                if x > 0.80 * ax.get_xlim()[1]:   # rechter Rand: Beschriftung nach links
                    dx = -dx
            jahr = z.get("Bezugsjahr")
            beschriftung = name if pd.isna(jahr) else f"{name} ({int(jahr)})"
            ax.annotate(beschriftung, (x, y), textcoords="offset points",
                        xytext=(dx, dy), fontsize=9, color=s["color"],
                        ha="left" if dx > 0 else "right", va="center", zorder=6,
                        bbox=dict(boxstyle="square,pad=0.12", facecolor="white",
                                  edgecolor="none", alpha=0.85),
                        arrowprops=dict(arrowstyle="-", color=s["color"], linewidth=0.7,
                                        shrinkA=1, shrinkB=7))
        if s["label"] not in gesehen:
            gesehen.add(s["label"])
            eintraege.append(Line2D([], [], linestyle="none", marker=s["marker"], markersize=9,
                                    markerfacecolor=s["color"], markeredgecolor=s["color"],
                                    label=s["label"]))
        i += 1
    ax.set_xlabel("Spannweite [m]")
    ax.set_ylabel(achsentitel)
    ax.set_title(titel, loc="left")
    ax.set_xlim(3, 7)
    ax.margins(y=0.12)
    ax.set_ylim(bottom=0)
    ax.grid(True, color="0.9", linewidth=0.6)
    ax.set_axisbelow(True)
    return eintraege


def main():
    pfad = neuestes_excel()
    print("Bestand:", pfad)
    df = pd.read_excel(pfad, sheet_name="Objekte")
    haupt_t, haupt_g = SPALTEN[VARIANTE]
    zweit = "KBOB" if VARIANTE == "EPD heute" else "EPD heute"
    zweit_t, zweit_g = SPALTEN[zweit]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), sharex=True)
    eintraege = zeichne(axes[0], df, haupt_t, zweit_t,
                        r"GWP$_{structure}$ [kg CO$_2$-eq / m$^2$]",
                        "a) tragende Schichten", teilbild="a")
    zeichne(axes[1], df, haupt_g, zweit_g,
            r"GWP$_{total}$ [kg CO$_2$-eq / m$^2$]",
            "b) total, inklusive Bodenaufbau", teilbild="b")

    # gleiche y-Achse in beiden Teilbildern, damit die Hoehen direkt vergleichbar sind
    y_max = max(ax.get_ylim()[1] for ax in axes)
    for ax in axes:
        ax.set_ylim(0, y_max)

    eintraege.append(Line2D([], [], linestyle="none", marker="o", markersize=9, markerfacecolor="white",
                            markeredgecolor="#333333", label="offen: Data Validation < 2"))
    if BEIDE_VARIANTEN:
        eintraege.append(Line2D([], [], color="#333333", marker="_", markersize=9, linewidth=1.0,
                                alpha=0.6, label=f"Bandbreite Betonannahme ({VARIANTE} … {zweit})"))

    fig.suptitle("Bestandesbauten: GWP über Spannweite", y=0.98)
    fig.legend(handles=eintraege, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.10, 1, 0.96))

    os.makedirs(DIAGRAMME, exist_ok=True)
    stempel = f"{date.today():%y%m%d}"
    for endung in ("png", "pdf"):
        ziel = os.path.join(DIAGRAMME, f"{stempel}_Bestand_Scatter.{endung}")
        fig.savefig(ziel, bbox_inches="tight")
        print("geschrieben:", ziel)
    plt.close(fig)


if __name__ == "__main__":
    main()
