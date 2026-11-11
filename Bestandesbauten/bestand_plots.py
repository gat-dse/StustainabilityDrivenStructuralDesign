# -*- coding: utf-8 -*-
"""
Diagramme GWP ueber Spannweite: Kurven des Deckenrechners mit Datenstreuung,
ergaenzt um die Punktwolke der analysierten Bestandesbauten.

Eingang:
  Workflow/Results/<Zeitstempel>_batch_1D.xlsx   aus 261111_Run_Kurven_1D.py  (SAVE_BATCH = True)
  Workflow/Results/<Zeitstempel>_batch_2D.xlsx   aus 261111_Run_Kurven_2D.py
  <Zeitstempel>_Bestandesanalyse_Wohnbauten.xlsx aus bestand_auswertung.py
Jeweils die neueste Datei wird verwendet, sofern nicht anders angegeben.

Ausgang:
  Diagramme/<Zeitstempel>_GWP_Struktur_mit_Bestand.(png|pdf)
  Diagramme/<Zeitstempel>_GWP_Struktur_und_Total_mit_Bestand.(png|pdf)

Linie   = Mittelwert ueber alle Produkte einer Gruppe bei gleicher Spannweite
Band    = kleinster und groesster Wert derselben Gruppe (Datenstreuung der EPD)
Punkte  = Bestandesbauten, ein Punkt je Objekt und Deckentyp
"""

import glob
import os
from datetime import date

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

HIER = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HIER, "..", "Workflow", "Results")
DIAGRAMME = os.path.join(HIER, "Diagramme")

SPANNWEITEN = (3, 12)          # dargestellter Bereich [m]
NUR_MACHBAR = True             # nur Querschnitte, die alle Nachweise erfuellen
MIT_BAND = True                # Datenstreuung als Band hinterlegen
BESTAND_VARIANTE = "EPD heute"  # "EPD heute" oder "KBOB" - welche Betonannahme die Punkte zeigen

# ----------------------------------------------------------------------------------------------------------------------
mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 13, "axes.labelsize": 13, "axes.titlesize": 13,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "legend.fontsize": 11,
    "figure.dpi": 110, "savefig.dpi": 300,
})

# Farben und Beschriftungen der Kurven, uebernommen aus
# Workflow/Results/Diagramme_Auswertung/260730_Auswertung_plots_1x2_GWP.py
KURVEN = {
    "Continuous 1D_rc_rec":   ("#000000", "o", "Vollplatte, einachsig tragend,\ndurchlaufend"),
    "Simple Beam_rc_rec":     ("#2ca02c", "o", "Vollplatte, einachsig tragend,\neinfach gelagert"),
    #"Simple Beam_rc_rib":     ("#9370db", "o", "Plattenbalken, einachsig tragend,\neinfach gelagert"),
    "2D_LL-eingespannt_rc_rec": ("#ffa042", "^", "Vollplatte, zweiachsig tragend,\ndurchlaufend"),
    "2D_LL-frei_rc_rec":      ("#8b0000", "^", "Vollplatte, zweiachsig tragend,\neinfach gelagert"),
}
AUFBAU_STIL = {"massiv": ("-", "Standardaufbau"), "Schuettung": ("--", "Standardaufbau + Schüttung")}

# Darstellung der Bestandespunkte nach Deckentyp
BESTAND_STIL = {
    "Stahlbeton-Flachdecke":  dict(marker="s", color="#1f4e79", label="Bestand: Stahlbeton-Flachdecke"),
    "Stahlbeton-Vollplatte":  dict(marker="s", color="#1f4e79", label="Bestand: Stahlbeton-Flachdecke"),
    "Holzbalkendecke":        dict(marker="D", color="#8c6d31", label="Bestand: Holzbalkendecke"),
    "Holz-Beton-Verbunddecke": dict(marker="P", color="#7f3f98", label="Bestand: Holz-Beton-Verbunddecke"),
    "Hourdisdecke":           dict(marker="X", color="#777777", label="Bestand: Hourdisdecke"),
}


def neueste(muster):
    # Sperrdateien von geoeffneten Excel-Arbeitsmappen ("~$...") ueberspringen
    treffer = sorted((p for p in glob.glob(muster) if not os.path.basename(p).startswith("~$")),
                     key=os.path.getmtime)
    if not treffer:
        return None
    return treffer[-1]


def lies_batch(pfad):
    """liest alle Ergebnisblaetter einer Batch-Datei (ein Blatt je Run, plus Blatt 'runs')"""
    if pfad is None:
        return pd.DataFrame()
    blaetter = pd.read_excel(pfad, sheet_name=None)
    teile = [df for name, df in blaetter.items() if name != "runs" and "l_tot [m]" in df.columns]
    if not teile:
        return pd.DataFrame()
    df = pd.concat(teile, ignore_index=True)
    df["quelle"] = os.path.basename(pfad)
    return df


def gruppen_schluessel(zeile):
    """fasst plot_label auf System und Querschnittstyp zusammen, ohne Bodenaufbau und Datenbasis"""
    label = str(zeile["plot_label"])
    for schluessel in KURVEN:
        if label.startswith(schluessel + "_"):
            return schluessel
    return None


def bereite_kurven(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    for spalte in ("l_tot [m]", "co2_struct [kgCO2eq/m2]", "co2_floor [kgCO2eq/m2]"):
        df[spalte] = pd.to_numeric(df[spalte], errors="coerce")
    df["co2_tot [kgCO2eq/m2]"] = df["co2_struct [kgCO2eq/m2]"] + df["co2_floor [kgCO2eq/m2]"]
    if NUR_MACHBAR and "feasible" in df.columns:
        df = df[df["feasible"].astype(str).str.lower().isin(["true", "1", "wahr"])]
    df = df.dropna(subset=["l_tot [m]", "co2_struct [kgCO2eq/m2]", "co2_floor [kgCO2eq/m2]"])
    df = df[df["l_tot [m]"].between(*SPANNWEITEN)]
    df["gruppe"] = df.apply(gruppen_schluessel, axis=1)
    df = df[df["gruppe"].notna()]
    return df


def zeichne_kurven(ax, df, y_spalte, nur_massiv):
    """zeichnet Mittelwertlinien und Streubaender; gibt die Legendeneintraege zurueck"""
    eintraege = []
    for (gruppe, aufbau), g in df.groupby(["gruppe", "floor"], sort=False):
        if nur_massiv and aufbau != "massiv":
            continue
        if gruppe not in KURVEN or aufbau not in AUFBAU_STIL:
            continue
        farbe, marker, text = KURVEN[gruppe]
        stil, aufbau_text = AUFBAU_STIL[aufbau]
        werte = g.groupby("l_tot [m]")[y_spalte].agg(["mean", "min", "max"]).sort_index()
        if MIT_BAND and nur_massiv:
            ax.fill_between(werte.index, werte["min"], werte["max"], color=farbe, alpha=0.12, zorder=1)
        ax.plot(werte.index, werte["mean"], color=farbe, linestyle=stil, marker=marker,
                markersize=4.5, markerfacecolor="white", markeredgecolor=farbe, linewidth=1.2, zorder=3)
        eintraege.append(Line2D([], [], color=farbe, linestyle=stil, marker=marker, markersize=5,
                                markerfacecolor="white", markeredgecolor=farbe,
                                label=f"{text}\n({aufbau_text})"))
    return eintraege


def lies_bestand(pfad):
    df = pd.read_excel(pfad, sheet_name="Objekte")
    spalte_struktur = ("GWP tragend, EPD heute [kg CO₂-eq/m²]" if BESTAND_VARIANTE == "EPD heute"
                       else "GWP tragend, KBOB [kg CO₂-eq/m²]")
    spalte_total = ("GWP total, EPD heute [kg CO₂-eq/m²]" if BESTAND_VARIANTE == "EPD heute"
                    else "GWP total, KBOB [kg CO₂-eq/m²]")
    df = df.rename(columns={"massgebende Spannweite [m]": "l", spalte_struktur: "co2_struct",
                            spalte_total: "co2_tot"})
    df = df.dropna(subset=["l", "co2_struct"])
    return df


def stil_fuer(deckentyp):
    for schluessel, stil in BESTAND_STIL.items():
        if str(deckentyp).startswith(schluessel):
            return stil
    return dict(marker="o", color="#333333", label="Bestand: übrige")


def zeichne_bestand(ax, bestand, y_spalte, beschriften=True):
    eintraege, gesehen = [], set()
    # Beschriftungen abwechselnd ueber und unter den Punkt setzen, damit sie sich weniger ueberdecken
    versatz = [(7, 5), (7, -11), (-7, 5), (-7, -11)]
    for i, (_, z) in enumerate(bestand.iterrows()):
        if pd.isna(z.get(y_spalte)):
            continue
        stil = stil_fuer(z["Deckentyp"])
        gefuellt = z["Data Validation"] >= 2
        ax.scatter(z["l"], z[y_spalte], marker=stil["marker"], s=75, zorder=5,
                   facecolors=stil["color"] if gefuellt else "white",
                   edgecolors=stil["color"], linewidths=1.6)
        if beschriften:
            dx, dy = versatz[i % len(versatz)]
            ax.annotate(str(z["Objekt"]).split(",")[0], (z["l"], z[y_spalte]),
                        textcoords="offset points", xytext=(dx, dy), fontsize=8, color=stil["color"],
                        ha="left" if dx > 0 else "right")
        if stil["label"] not in gesehen:
            gesehen.add(stil["label"])
            eintraege.append(Line2D([], [], linestyle="none", marker=stil["marker"], markersize=8,
                                    markerfacecolor=stil["color"], markeredgecolor=stil["color"],
                                    label=stil["label"]))
    eintraege.append(Line2D([], [], linestyle="none", marker="o", markersize=8, markerfacecolor="white",
                            markeredgecolor="#333333", label="offen: Data Validation < 2"))
    return eintraege


# ----------------------------------------------------------------------------------------------------------------------
def main():
    batch_1d = neueste(os.path.join(RESULTS, "*_batch_1D.xlsx"))
    batch_2d = neueste(os.path.join(RESULTS, "*_batch_2D.xlsx"))
    bestand_xlsx = neueste(os.path.join(HIER, "*_Bestandesanalyse_Wohnbauten.xlsx"))
    if bestand_xlsx is None:
        raise FileNotFoundError("Bestandesanalyse-Excel nicht gefunden. Zuerst bestand_auswertung.py laufen lassen.")
    if batch_1d is None and batch_2d is None:
        raise FileNotFoundError(
            "Keine Batch-Ergebnisse in Workflow/Results gefunden.\n"
            "Zuerst 261111_Run_Kurven_1D.py und 261111_Run_Kurven_2D.py aus dem Ordner Workflow/ laufen lassen.")
    print("Kurven 1D:", batch_1d)
    print("Kurven 2D:", batch_2d)
    print("Bestand  :", bestand_xlsx)

    df = bereite_kurven(pd.concat([lies_batch(batch_1d), lies_batch(batch_2d)], ignore_index=True))
    bestand = lies_bestand(bestand_xlsx)
    os.makedirs(DIAGRAMME, exist_ok=True)
    stempel = f"{date.today():%y%m%d}"

    # -------------------------------------------------- Diagramm 1: nur Struktur, mit Streuband
    fig, ax = plt.subplots(figsize=(11, 7.5))
    eintraege = zeichne_kurven(ax, df, "co2_struct [kgCO2eq/m2]", nur_massiv=True)
    eintraege += zeichne_bestand(ax, bestand, "co2_struct")
    ax.set_xlabel("Spannweite [m]")
    ax.set_ylabel(r"GWP$_{structure}$ [kg CO$_{2eq}$ / m$^2$]")
    ax.set_title("GWP Struktur inkl. Datenstreuung, mit Bestandesbauten (Bodenaufbau Standard)")
    ax.set_xlim(*SPANNWEITEN)
    ax.set_ylim(bottom=0)
    ax.grid(True, color="0.9", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.legend(handles=eintraege, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.20, 1, 1))
    for endung in ("png", "pdf"):
        fig.savefig(os.path.join(DIAGRAMME, f"{stempel}_GWP_Struktur_mit_Bestand.{endung}"), bbox_inches="tight")
    plt.close(fig)

    # -------------------------------------------------- Diagramm 2: Struktur und Total nebeneinander
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    eintraege = []
    for ax, y_kurve, y_punkt, titel, achse in [
            (axes[0], "co2_struct [kgCO2eq/m2]", "co2_struct", "a)", r"GWP$_{structure}$ [kg CO$_2$-eq / m$^2$]"),
            (axes[1], "co2_tot [kgCO2eq/m2]", "co2_tot", "b)", r"GWP$_{total}$ [kg CO$_2$-eq / m$^2$]")]:
        e = zeichne_kurven(ax, df, y_kurve, nur_massiv=False)
        e += zeichne_bestand(ax, bestand, y_punkt, beschriften=False)
        if not eintraege:
            eintraege = e
        ax.set_xlabel("Spannweite [m]")
        ax.set_ylabel(achse)
        ax.set_title(titel, loc="left")
        ax.set_xlim(*SPANNWEITEN)
        ax.set_ylim(bottom=0)
        ax.grid(True, color="0.9", linewidth=0.6)
        ax.set_axisbelow(True)
    fig.suptitle("Kurven des Deckenrechners und Bestandesbauten (3...12 m)")
    fig.legend(handles=eintraege, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.22, 1, 0.97))
    for endung in ("png", "pdf"):
        fig.savefig(os.path.join(DIAGRAMME, f"{stempel}_GWP_Struktur_und_Total_mit_Bestand.{endung}"),
                    bbox_inches="tight")
    plt.close(fig)
    print("Diagramme geschrieben nach:", DIAGRAMME)


if __name__ == "__main__":
    main()
