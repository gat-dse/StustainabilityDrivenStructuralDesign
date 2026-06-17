import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ==============================================================================
# GLOBALE EINSTELLUNGEN & DATENPREPARATION
# ==============================================================================
excel_file = "260611_1515_Members.xlsx"
df = pd.read_excel(excel_file)

x_achse = 'l_tot [m]'
y_struc_h = 'h_QS [m]'  # Höhe der Struktur
kategorie_1 = 'plot_label'
kategorie_2 = 'Bodenaufbau'

# Datentypen erzwingen
df[x_achse] = pd.to_numeric(df[x_achse], errors='coerce')
df[y_struc_h] = pd.to_numeric(df[y_struc_h], errors='coerce')

# Bereinigen & Filtern: Spannweite 3 bis 12 m & NUR massiver Bodenaufbau
pflicht_spalten = [x_achse, kategorie_1, kategorie_2, y_struc_h]
df_clean = df.dropna(subset=pflicht_spalten).copy()

df_filtered = df_clean[
    (df_clean[x_achse].between(3, 12)) &
    (df_clean[kategorie_2].str.lower() == 'massiv')
].copy()

# Aggregation: Mittelwerte für die Linienplots berechnen
df_grouped = df_filtered.groupby([x_achse, kategorie_1], as_index=False)[y_struc_h].mean()

# ==============================================================================
# UNIFORMES DESIGN-MAPPING (FARBEN & MARKER)
# ==============================================================================
farb_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': '#000000',  # Schwarz als Referenz
    'BeamSimpleSup_rc_rec_massiv': '#2ca02c',       # Grün (Rechteck)
    'BeamSimpleSup_rc_rib_massiv': '#9370db',       # Violett (Plattenbalken)
    'Slab_LL-eingespannt_rc_rec_massiv': '#ffa042', # Orange (Eingespannt)
    'Slab_LL-frei_rc_rec_massiv': '#8b0000'         # Dunkelrot (Frei)
}

marker_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rec_massiv': 'o',
    'BeamSimpleSup_rc_rib_massiv': 'o',
    'Slab_LL-eingespannt_rc_rec_massiv': '^',
    'Slab_LL-frei_rc_rec_massiv': '^'
}

legend_label_mapping = {
    'BeamContinuousSupEl_rc_rec_massiv': 'Durchlaufträger, Rechteck',
    'BeamSimpleSup_rc_rec_massiv': 'Einfeldträger, Rechteck',
    'BeamSimpleSup_rc_rib_massiv': 'Einfeldträger, Plattenbalken',
    'Slab_LL-eingespannt_rc_rec_massiv': 'Platte, eingespannt',
    'Slab_LL-frei_rc_rec_massiv': 'Platte, frei aufliegend'
}

L_WIDTH_GLOBAL = 1.0
M_SIZE_GLOBAL = 5.0

def apply_clean_grid(ax):
    ax.grid(True, linestyle='-', color='#e0e0e0', linewidth=0.4)

# ==============================================================================
# PLOT GENERIEREN
# ==============================================================================
fig = plt.figure(figsize=(11, 8.5))
sns.set_theme(style="whitegrid")

# GridSpec für saubere Platzierung der Legende unterhalb
gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 0.22],
                      left=0.10, right=0.95, top=0.91, bottom=0.05, hspace=0.25)

ax = fig.add_subplot(gs[0])
ax_leg = fig.add_subplot(gs[1])
ax_leg.axis('off')

# Sortieren für konsistenten Linienverlauf
df_grouped = df_grouped.sort_values(by=[kategorie_1, x_achse])

# Alle Systeme plotten
for label, g in df_grouped.groupby(kategorie_1):
    farbe = farb_mapping.get(label, '#7f7f7f')
    schoener_name = legend_label_mapping.get(label, label)
    marker_style = marker_mapping.get(label, 'o')

    ax.plot(g[x_achse], g[y_struc_h], marker=marker_style, markersize=M_SIZE_GLOBAL,
            markeredgewidth=0.5, markeredgecolor='black', color=farbe,
            linestyle='-', linewidth=L_WIDTH_GLOBAL, label=schoener_name)

# --- HORIZONTALE LINIE FÜR SCHALLSCHUTZ MIT LEGENDEN-EINTRAG ---
h_schallschutz = 0.24  # 24 cm in Metern
ax.axhline(y=h_schallschutz, color='#d32f2f', linestyle='--', linewidth=1.2,
           label='Mindeststärke erhöhte Anforderung Schallschutz (24 cm)')

# --- ERGÄNZUNG: '0.24' DYNAMISCH AUF DER Y-ACHSE ANZEIGEN ---
ax.set_ylim(bottom=0)
current_ticks = list(ax.get_yticks())
# Füge 0.24 hinzu, falls es nicht ohnehin exakt getroffen wird, und sortiere die Liste
if h_schallschutz not in current_ticks:
    current_ticks.append(h_schallschutz)
current_ticks = sorted(list(set(current_ticks)))

ax.set_yticks(current_ticks)

# Formatierung der Ticks auf der Y-Achse, damit 0.24 farblich hervorgehoben wird (optional)
labels = [f"{tick:.2f}" if tick != h_schallschutz else f"0.24" for tick in current_ticks]
ax.set_yticklabels(labels)

# Optionale farbliche Kennzeichnung des Ticks '0.24' auf der Y-Achse
for t in ax.get_yticklabels():
    if "Ref" in t.get_text():
        t.set_color('#d32f2f')
        t.set_weight('bold')

# Achsen-Konfiguration
ax.set_xlim(3, 12)
ax.set_title("Strukturhöhe ($h_{struc}$) im Systemvergleich (3-12m, massiv)", fontsize=13, fontweight='bold', pad=15)
ax.set_xlabel("Spannweite [m]", fontsize=11)
ax.set_ylabel("Strukturhöhe $h_{struc}$ [m]", fontsize=11)

apply_clean_grid(ax)

# Legende im unteren Bereich generieren (jetzt inkl. der Schallschutz-Referenzlinie)
handles, labels = ax.get_legend_handles_labels()
ax_leg.legend(handles, labels, title="Tragsysteme (Bodenaufbau: massiv)",
              loc="upper center", ncol=2, fontsize='medium', title_fontsize='medium', frameon=True)

# Plot speichern und anzeigen
filename = "Strukturhoehe_Systemvergleich_3-12m.png"
plt.savefig(filename, dpi=300)
print(f"Plot erfolgreich gespeichert unter: {filename}")

plt.show()