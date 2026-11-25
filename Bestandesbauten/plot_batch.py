# -*- coding: utf-8 -*-
"""
Zeichnet eine oder mehrere Batch-Dateien des Deckenrechners.

Aufruf:
    python plot_batch.py                          neueste *_batch_1D.xlsx und *_batch_2D.xlsx
    python plot_batch.py 261125_1209_batch_1D.xlsx           genau diese Datei
    python plot_batch.py datei1.xlsx datei2.xlsx             mehrere zusammen

Dateinamen ohne Pfad werden in Workflow/Results gesucht.

Ausgang: Bestandesbauten/Diagramme/<Zeitstempel>_Kurven.(png|pdf)
Linie = Mittelwert ueber alle Produkte einer Gruppe, Band = kleinster und groesster Wert.
"""

import glob
import os
import sys
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

HIER = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HIER, "..", "Workflow", "Results"))
DIAGRAMME = os.path.join(HIER, "Diagramme")

NUR_MACHBAR = True   # False: auch Querschnitte zeichnen, die Nachweise verletzen
MIT_BAND = True      # Streuung der Produkte als Band hinterlegen

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 13, "axes.labelsize": 13, "axes.titlesize": 13,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 10,
    "figure.dpi": 110, "savefig.dpi": 300,
})

# Farbe, Marker und Beschriftung je System; unbekannte Datensaetze bekommen automatisch eine Farbe
STIL = {
    "Continuous 1D_rc_rec":     ("#000000", "o", "Vollplatte, einachsig, durchlaufend"),
    "Simple Beam_rc_rec":       ("#2ca02c", "o", "Vollplatte, einachsig, einfach gelagert"),
    "Two span 1D 1D_rc_rec":    ("#1f77b4", "o", "Vollplatte, einachsig, Zweifeldträger"),
    "Simple Beam_rc_rib":       ("#9370db", "o", "Plattenbalken, einachsig, einfach gelagert"),
    "Continuous 1D_rc_rib":     ("#5b3f91", "o", "Plattenbalken, einachsig, durchlaufend"),
    "Simple Beam_wd_rec":       ("#8c6d31", "s", "Massivholzdecke, einfach gelagert"),
    "Simple Beam_wd_rib":       ("#d62728", "s", "Hohlkastendecke, einfach gelagert"),
    "2D_LL-frei_rc_rec":        ("#8b0000", "^", "Vollplatte, zweiachsig, einfach gelagert"),
    "2D_LL-eingespannt_rc_rec": ("#ffa042", "^", "Vollplatte, zweiachsig, durchlaufend"),
    "2D_PL-eingespannt_rc_rec": ("#c77dff", "^", "Vollplatte, punktgestützt, eingespannt"),
}
AUFBAU = {"massiv": ("-", "Standardaufbau"), "Schuettung": ("--", "Standardaufbau + Schüttung"),
          "Vollholz": ("-", "Vollholzaufbau"), "Hohlkasten": ("-", "Hohlkastenaufbau")}
ERSATZFARBEN = ["#17becf", "#bcbd22", "#e377c2", "#7f7f7f", "#ff7f0e"]


def dateien_waehlen(argumente):
    """Dateiliste aus den Aufrufargumenten, sonst die neueste 1D- und 2D-Batchdatei"""
    if argumente:
        pfade = []
        for a in argumente:
            p = a if os.path.isabs(a) or os.path.dirname(a) else os.path.join(RESULTS, a)
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Datei nicht gefunden: {p}")
            pfade.append(p)
        return pfade
    pfade = []
    for muster in ("*_batch_1D.xlsx", "*_batch_2D.xlsx"):
        treffer = sorted((p for p in glob.glob(os.path.join(RESULTS, muster))
                          if not os.path.basename(p).startswith("~$")), key=os.path.getmtime)
        if treffer:
            pfade.append(treffer[-1])
    if not pfade:
        raise FileNotFoundError(f"Keine Batch-Dateien in {RESULTS}. Zuerst einen Lauf starten.")
    return pfade


def lesen(pfade):
    teile = []
    for p in pfade:
        for name, df in pd.read_excel(p, sheet_name=None).items():
            if name == "runs" or "l_tot [m]" not in df.columns:
                continue
            df = df.copy()
            df["quelle"] = os.path.basename(p)
            teile.append(df)
    if not teile:
        raise ValueError("Die gewaehlten Dateien enthalten keine Ergebnisblaetter.")
    df = pd.concat(teile, ignore_index=True)

    for spalte in ("l_tot [m]", "co2_struct [kgCO2eq/m2]", "co2_floor [kgCO2eq/m2]"):
        df[spalte] = pd.to_numeric(df[spalte], errors="coerce")
    df["co2_tot [kgCO2eq/m2]"] = df["co2_struct [kgCO2eq/m2]"] + df["co2_floor [kgCO2eq/m2]"]
    df = df.dropna(subset=["l_tot [m]", "co2_struct [kgCO2eq/m2]"])

    if NUR_MACHBAR and "feasible" in df.columns:
        vorher = len(df)
        df = df[df["feasible"].astype(str).str.lower().isin(["true", "1", "wahr"])]
        print(f"  {vorher - len(df)} von {vorher} Querschnitten verletzen Nachweise und werden weggelassen")

    # plot_label = <System>_<Querschnitt>_<Bodenaufbau>_<Datenbasis> -> System+Querschnitt und Bodenaufbau trennen
    def gruppe(label):
        teile = str(label).split("_")
        return "_".join(teile[:-2]) if len(teile) > 2 else str(label)
    df["gruppe"] = df["plot_label"].map(gruppe)
    if "floor" not in df.columns:
        df["floor"] = "massiv"
    return df


def zeichnen(ax, df, y_spalte, achsentitel, titel):
    eintraege, frei = [], list(ERSATZFARBEN)
    for (gruppe, aufbau), g in sorted(df.groupby(["gruppe", "floor"], sort=False), key=lambda x: str(x[0])):
        if gruppe in STIL:
            farbe, marker, text = STIL[gruppe]
        else:
            farbe, marker, text = (frei.pop(0) if frei else "#444444"), "o", str(gruppe)
        stil, aufbau_text = AUFBAU.get(aufbau, ("-", str(aufbau)))
        werte = g.groupby("l_tot [m]")[y_spalte].agg(["mean", "min", "max"]).sort_index()
        if werte.empty:
            continue
        if MIT_BAND:
            ax.fill_between(werte.index, werte["min"], werte["max"], color=farbe, alpha=0.12, zorder=1)
        ax.plot(werte.index, werte["mean"], color=farbe, linestyle=stil, marker=marker, markersize=4.5,
                markerfacecolor="white", markeredgecolor=farbe, linewidth=1.3, zorder=3)
        eintraege.append(Line2D([], [], color=farbe, linestyle=stil, marker=marker, markersize=5,
                                markerfacecolor="white", markeredgecolor=farbe,
                                label=f"{text}\n({aufbau_text})"))
    ax.set_xlabel("Spannweite [m]")
    ax.set_ylabel(achsentitel)
    ax.set_title(titel, loc="left")
    ax.set_ylim(bottom=0)
    ax.grid(True, color="0.9", linewidth=0.6)
    ax.set_axisbelow(True)
    return eintraege


def sichern(fig, basis):
    """speichert PNG und PDF; haengt einen Zaehler an, falls die Datei gerade geoeffnet ist"""
    for endung in ("png", "pdf"):
        ziel = f"{basis}.{endung}"
        for versuch in range(1, 5):
            try:
                fig.savefig(ziel, bbox_inches="tight")
                print("  geschrieben:", ziel)
                break
            except PermissionError:
                ziel = f"{basis}_{versuch}.{endung}"
        else:
            print(f"  NICHT geschrieben: {basis}.{endung} ist gesperrt (in einem Programm geoeffnet?)")


def main():
    pfade = dateien_waehlen(sys.argv[1:])
    print("Gelesen:")
    for p in pfade:
        print(f"  {p}   ({datetime.fromtimestamp(os.path.getmtime(p)):%d.%m.%Y %H:%M})")
    df = lesen(pfade)
    print(f"  {len(df)} Querschnitte, {df['gruppe'].nunique()} Systeme, "
          f"Spannweiten {df['l_tot [m]'].min():g}...{df['l_tot [m]'].max():g} m")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    eintraege = zeichnen(axes[0], df, "co2_struct [kgCO2eq/m2]",
                         r"GWP$_{structure}$ [kg CO$_2$-eq / m$^2$]", "a) tragende Schichten")
    zeichnen(axes[1], df, "co2_tot [kgCO2eq/m2]",
             r"GWP$_{total}$ [kg CO$_2$-eq / m$^2$]", "b) total, inklusive Bodenaufbau")
    y_max = max(ax.get_ylim()[1] for ax in axes)
    for ax in axes:
        ax.set_ylim(0, y_max)

    fig.suptitle("Deckenrechner: GWP über Spannweite", y=0.98)
    fig.legend(handles=eintraege, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.14, 1, 0.96))

    os.makedirs(DIAGRAMME, exist_ok=True)
    stempel = datetime.now().strftime("%y%m%d_%H%M")
    sichern(fig, os.path.join(DIAGRAMME, f"{stempel}_Kurven"))
    plt.close(fig)


if __name__ == "__main__":
    main()
