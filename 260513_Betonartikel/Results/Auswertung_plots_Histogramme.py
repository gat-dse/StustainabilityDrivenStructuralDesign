import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Datei einlesen (Pfad ggf. anpassen)
excel_file = "260604_RC_1D_Systems.xlsx"
df = pd.read_excel(excel_file)


# ==============================================================================
# FUNKTION FÜR DEN FLEXIBLEN GESTAPELTEN BALKENPLOT
# ==============================================================================
def erstelle_gestapelten_balkenplot(data,
                                    komponente_unten,
                                    excel_dateiname,  # Für die automatische Namensgebung
                                    komponente_oben=None,
                                    label_unten="Struktur",
                                    label_oben="Bodenaufbau",
                                    y_achsen_titel="Wert",
                                    diagramm_titel="Diagramm"):
    """
    Erstellt ein gruppiertes und gestapeltes Balkendiagramm sortiert nach Spannweiten
    und speichert es automatisch ab.
    """
    # Lokale Kopie erstellen, um das originale df nicht zu verändern
    df_temp = data.copy()

    x_achse = 'plot_label'
    kategorie_1 = 'l_tot [m]'

    # Relevante Spalten numerisch konvertieren
    df_temp[kategorie_1] = pd.to_numeric(df_temp[kategorie_1], errors='coerce')
    df_temp[komponente_unten] = pd.to_numeric(df_temp[komponente_unten], errors='coerce')

    pflicht_spalten = [x_achse, kategorie_1, komponente_unten]

    if komponente_oben:
        df_temp[komponente_oben] = pd.to_numeric(df_temp[komponente_oben], errors='coerce')
        pflicht_spalten.append(komponente_oben)

    # Daten bereinigen
    df_filtered = df_temp.dropna(subset=pflicht_spalten)

    # Mittelwerte über die Kombination aus Querschnitt AND Spannweite bilden
    aggregations_dict = {komponente_unten: 'mean'}
    if komponente_oben:
        aggregations_dict[komponente_oben] = 'mean'

    df_plot = df_filtered.groupby([x_achse, kategorie_1]).agg(aggregations_dict).reset_index()

    # Sortieren nach Spannweite und Querschnitt
    df_plot = df_plot.sort_values(by=[kategorie_1, x_achse], ascending=[True, True])

    # Einzigartige Spannweiten und Querschnitte ermitteln
    einzigartige_spannweiten = sorted(df_plot[kategorie_1].unique())
    einzigartige_qs = df_plot[x_achse].unique()

    # Farb-Mapping für die Querschnitte generieren
    farben = sns.color_palette("viridis", len(einzigartige_qs))
    farb_mapping = dict(zip(einzigartige_qs, farben))

    # --- HIER DEINE GEWÜNSCHTEN ABSTÄNDE UND BREITEN ---
    balken_breite = 0.14
    balken_abstand = 0.03
    abstand_zwischen_gruppen = 2.0

    plt.figure(figsize=(24, 8))
    sns.set_theme(style="whitegrid")
    # ----------------------------------------------------

    tick_positionen = []
    tick_labels = []

    # Loop über alle Spannweiten-Blöcke
    for j, spannweite in enumerate(einzigartige_spannweiten):
        df_spannweite = df_plot[df_plot[kategorie_1] == spannweite]

        gruppen_zentrum = j * abstand_zwischen_gruppen
        tick_positionen.append(gruppen_zentrum)
        tick_labels.append(f"{spannweite} m")

        anzahl_balken = len(df_spannweite)
        gesamt_breite_gruppe = (anzahl_balken * balken_breite) + ((anzahl_balken - 1) * balken_abstand)
        start_x = gruppen_zentrum - gesamt_breite_gruppe / 2 + balken_breite / 2

        for idx, (index, row) in enumerate(df_spannweite.iterrows()):
            qs_typ = row[x_achse]
            basis_farbe = farb_mapping[qs_typ]

            balken_x = start_x + idx * (balken_breite + balken_abstand)

            # Balken 1: Untere Komponente (Vollflächig, Dunkel)
            plt.bar(
                balken_x,
                row[komponente_unten],
                width=balken_breite,
                color=basis_farbe,
                edgecolor='black',
                linewidth=1,
                alpha=1.0
            )

            # Balken 2: Obere Komponente (Schraffiert + Hell), falls übergeben
            if komponente_oben:
                plt.bar(
                    balken_x,
                    row[komponente_oben],
                    bottom=row[komponente_unten],
                    width=balken_breite,
                    color=basis_farbe,
                    edgecolor='black',
                    hatch='\\\\\\\\',
                    linewidth=1,
                    alpha=0.45
                )

    # --- LEGENDEN KONFIGURATION ---
    aus_patches = [plt.Rectangle((0, 0), 1, 1, facecolor=farb_mapping[qs], edgecolor='black') for qs in einzigartige_qs]
    legende_qs = plt.legend(aus_patches, einzigartige_qs, title="Querschnitt-Varianten", bbox_to_anchor=(1.02, 1),
                            loc='upper left', fontsize='small')

    gwp_patches = [plt.Rectangle((0, 0), 1, 1, facecolor='gray', edgecolor='black', alpha=1.0)]
    gwp_labels = [label_unten]

    if komponente_oben:
        gwp_patches.append(
            plt.Rectangle((0, 0), 1, 1, facecolor='gray', edgecolor='black', alpha=0.45, hatch='\\\\\\\\'))
        gwp_labels.append(label_oben)

    legende_gwp = plt.legend(gwp_patches, gwp_labels, title="Komponenten", bbox_to_anchor=(1.02, 0.4),
                             loc='upper left', fontsize='small')

    plt.gca().add_artist(legende_qs)

    # --- FINETUNING & ACHSEN ---
    plt.title(diagramm_titel, fontsize=14, fontweight='bold')
    plt.ylabel(y_achsen_titel, fontsize=12)
    plt.xlabel("Spannweite", fontsize=12)

    plt.xticks(tick_positionen, tick_labels, fontsize=11, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.5, axis='y')

    plt.tight_layout(rect=[0, 0, 0.75, 0.95])

    # --- AUTOMATISCHES SPEICHERN ---
    basis_name = os.path.splitext(os.path.basename(excel_dateiname))[0]
    sauberer_titel = re.sub(r'[^\w\-_\. ]', '', diagramm_titel).replace(' ', '_')
    speicher_name = f"{basis_name}_{sauberer_titel}.png"

    plt.savefig(speicher_name, dpi=300, bbox_inches='tight')
    print(f"Diagramm erfolgreich gespeichert als: {speicher_name}")

    plt.show()


# ==============================================================================
# ANWENDUNGSBEISPIELE
# ==============================================================================

# Beispiel 1: GWP
erstelle_gestapelten_balkenplot(
    data=df,
    excel_dateiname=excel_file,
    komponente_unten='co2 Struktur [kgCO2eq/m2]',
    komponente_oben='co2 Bodenaufbau [kgCO2eq/m2]',
    label_unten='GWP Struktur (Dunkel / Glatt)',
    label_oben='GWP Bodenaufbau (Hell / Schraffiert)',
    y_achsen_titel='GWP [kgCO2eq / m²]',
    diagramm_titel='GWP-Aufteilung sortiert nach Spannweiten'
)

# Beispiel 2: Lasten
erstelle_gestapelten_balkenplot(
    data=df,
    excel_dateiname=excel_file,
    komponente_unten='Last Struktur [kN/m2]',
    komponente_oben='Last Bodenaufbau [kN/m2]',
    label_unten='Last Struktur (Dunkel / Glatt)',
    label_oben='Last Bodenaufbau (Hell / Schraffiert)',
    y_achsen_titel='Last [kN/m²]',
    diagramm_titel='Lasten-Aufteilung sortiert nach Spannweiten'
)