import os
import glob
import pandas as pd
from datetime import datetime

# ==============================================================================
# CONFIGURATION & DEFINITIONS
# ==============================================================================

# Ziel-Struktur für die finale Datenbank (Schritt 2)
target_columns = [
    "Member_ID", "criteria", "section_type", "Statisches System", "Raender" , "l_tot [m]",
    "h_QS [m]", "b [m]", "b_w [m]", "h_f [m]",
    "Bew_Gehalt [kg/m3]", "MEd_n [kNm]", "MEd_p [kNm]", "VEd [kN]",
    "concrete_type", "mech_prop", "prod_id", "GWP concrete [kgCO2eq / t]",
    "rebar_type", "mech_prop_1", "prod_id_1", "GWP rebar [kgCO2eq / t]",
    "co2_rebar [kgCO2eq/m2]", "co2_concrete [kgCO2eq/m2]", "co2 Struktur [kgCO2eq/m2]",
    "Bodenaufbau", "lifespan Estrich [a]", "h_Bodenaufbau [m]", "co2 Bodenaufbau [kgCO2eq/m2]",
    "co2 Bodenaufbau pro Jahr [kgCO2eq/m2a]", "Last Struktur [N/m2]",
    "Last Bodenaufbau [N/m2]", "co2 [kgco2eq/m2]", "co2 pro Jahr [kgco2eq/m2a]"
]


# ==============================================================================
# SCHRITT 1: FUNKTION FÜR DAS CLEANING DER EINZELNEN ROHDATEIEN
# ==============================================================================
def clean_single_member_file(file_path):
    """Liest ein Roh-Excel, transponiert es, bereinigt Spalten und speichert die _clean.xlsx"""
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Fehler beim Lesen von {file_path}: {e}")
        return None

    # Transponieren
    df_clean = df.set_index(['key', 'level']).T
    df_clean.index.name = 'Member_ID'
    df_clean.columns = df_clean.columns.get_level_values(0)
    df_clean = df_clean.reset_index()

    # Spaltennamen eindeutig machen bei Duplikaten
    cols = pd.Series(df_clean.columns)
    for i in cols[cols.duplicated()].unique():
        cols[cols[cols == i].index] = [f"{i}_{count}" if count != 0 else i
                                       for count in range(len(cols[cols == i]))]
    df_clean.columns = cols

    # EINHEITENKONVERTIERUNG (Nm -> kNm und N -> kN) ---
    for col in ['mEd_n', 'mEd_p', 'vEd']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce') / 1000

    # Relevante Spalten definieren
    if 'rc_rec' in df_clean['section_type'].values:
        spalten_fokus = ['Member_ID', 'section_type', 'l_tot', 'h', 'b',
                         'Bew_Gehalt', 'mEd_n', 'mEd_p', 'vEd',
                         'concrete_type', 'mech_prop', 'prod_id', 'GWP',
                         'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1', 'co2_rebar', 'co2_concrete', 'co2',
                         'system', 'raender', 'name', 'lifespan_1',
                         'h_Floor', 'co2_Floor', 'co2_a_Floor', 'g0k_b_1', 'g1k', 'co2_1', 'co2_a']
        spalten_neu = ['Member_ID', 'section_type', 'l_tot [m]', 'h_QS [m] ', 'b [m]',
                       'Bew_Gehalt [kg/m3]', 'MEd_n [kNm]', 'MEd_p [kNm]', 'VEd [kN]',
                       'concrete_type', 'mech_prop',
                       'prod_id', 'GWP concrete [kgCO2eq / t]', 'rebar_type', 'mech_prop_1', 'prod_id_1',
                       'GWP rebar [kgCO2eq / t]',
                       'co2_rebar [kgCO2eq/m2]', 'co2_concrete [kgCO2eq/m2]', 'co2 Struktur [kgCO2eq/m2]',
                       'Statisches System', 'Raender', 'Bodenaufbau', 'lifespan Estrich [a]',
                       'h_Bodenaufbau [m]', 'co2 Bodenaufbau [kgCO2eq/m2]', 'co2 Bodenaufbau pro Jahr [kgCO2eq/m2a]',
                       'Last Struktur [N/m2]', 'Last Bodenaufbau [N/m2]', 'co2 Bauteil [kgCO2eq/m]',
                       'co2 Bauteil pro Jahr [kgCO2eq/ma]']
    elif 'rc_rib' in df_clean['section_type'].values:
        spalten_fokus = ['Member_ID', 'section_type', 'l_tot', 'h', 'b', 'b_w', 'h_f',
                         'Bew_Gehalt', 'mEd_n', 'mEd_p', 'vEd',
                         'concrete_type', 'mech_prop', 'prod_id', 'GWP',
                         'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP_1',
                         'co2_rebar', 'co2_concrete', 'co2',
                         'system', 'raender', 'name', 'lifespan_1',
                         'h_Floor', 'co2_Floor', 'co2_a_Floor', 'g0k_b_1', 'g1k', 'co2_1', 'co2_a']
        spalten_neu = ['Member_ID', 'section_type', 'l_tot [m]', 'h_QS [m] ', 'b [m]', 'b_w [m]', 'h_f [m]',
                       'Bew_Gehalt [kg/m3]', 'MEd_n [kNm]', 'MEd_p [kNm]', 'VEd [kN]',
                       'concrete_type', 'mech_prop', 'prod_id', 'GWP concrete [kgCO2eq / t]',
                       'rebar_type', 'mech_prop_1', 'prod_id_1', 'GWP rebar [kgCO2eq / t]',
                       'co2_rebar [kgCO2eq/m2]', 'co2_concrete [kgCO2eq/m2]', 'co2 Struktur [kgCO2eq/m2]',
                       'Statisches System', 'Raender', 'Bodenaufbau', 'lifespan Estrich [a]',
                       'h_Bodenaufbau [m]', 'co2 Bodenaufbau [kgCO2eq/m2]', 'co2 Bodenaufbau pro Jahr [kgCO2eq/m2a]',
                       'Last Struktur [N/m2]', 'Last Bodenaufbau [N/m2]', 'co2 Bauteil [kgCO2eq/m]',
                       'co2 Bauteil pro Jahr [kgCO2eq/ma]']
    else:
        print(f"-> Übersprungen: Unbekannter Bauteiltyp in {file_path}")
        return None

    # Sicheres Filtern & Umbenennen
    vorhandene_spalten = [c for c in spalten_fokus if c in df_clean.columns]
    df_final = df_clean[vorhandene_spalten].copy()
    rename_dict = {alt: neu for alt, neu in zip(spalten_fokus, spalten_neu) if alt in vorhandene_spalten}
    df_final = df_final.rename(columns=rename_dict)

    df_final = df_final[[n for n in spalten_neu if n in df_final.columns]]
    df_final.insert(1, 'criteria', 'ENV')

    for col in ['l_tot [m]', 'co2 Bauteil [kgCO2eq/m]', 'co2 Bauteil pro Jahr [kgCO2eq/ma]']:
        if col in df_final.columns:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

    if 'l_tot [m]' in df_final.columns and 'co2 Bauteil [kgCO2eq/m]' in df_final.columns:
        df_final['co2 [kgco2eq/m2]'] = df_final['co2 Bauteil [kgCO2eq/m]'] / df_final['l_tot [m]']
    if 'l_tot [m]' in df_final.columns and 'co2 Bauteil pro Jahr [kgCO2eq/ma]' in df_final.columns:
        df_final['co2 pro Jahr [kgco2eq/m2a]'] = df_final['co2 Bauteil pro Jahr [kgCO2eq/ma]'] / df_final['l_tot [m]']

    file_name_base = os.path.splitext(file_path)[0]
    output_clean_file = f"{file_name_base}_clean.xlsx"
    df_final.to_excel(output_clean_file, index=False)
    print(f"-> Erfolgreich bereinigt: {output_clean_file}")
    return output_clean_file


# ==============================================================================
# MAIN PIPELINE EXECUTION
# ==============================================================================
if __name__ == "__main__":

    print("=== SCHRITT 1: Bereinige Rohdaten-Excel ===")
    raw_files = [f for f in glob.glob("Members_*.xlsx") if "_clean" not in f]

    clean_files_pool = []
    for raw_file in raw_files:
        output_path = clean_single_member_file(raw_file)
        if output_path:
            clean_files_pool.append(output_path)

    if not clean_files_pool:
        print("Keine zu bereinigenden Rohdateien gefunden!")

    print("\n=== SCHRITT 2: Zusammenführen zur Master-Datenbank ===")
    cleaned_dfs = []

    for file in clean_files_pool:
        print(f"Lese bereinigte Datei ein: {file}")
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        df_reindexed = df.reindex(columns=target_columns)
        cleaned_dfs.append(df_reindexed)

    if cleaned_dfs:
        df_master = pd.concat(cleaned_dfs, axis=0, ignore_index=True)

        # --- NEU: TEXT-KOMBINATION & ÜBERSCHREIBEN DER SPALTE "Statisches System" ---
        # .fillna('') sorgt dafür, dass leere Zellen ignoriert werden und kein "nan" im Text steht.
        # .strip('_') entfernt den Unterstrich am Ende, falls keine Ränder vorhanden waren.
        df_master['Statisches System'] = (
                df_master['Statisches System'].astype(str).fillna('') + "_" + df_master['Raender'].fillna('').astype(
            str)
        ).str.strip('_')

        # Die separate Spalte "Raender" löschen, da sie nun integriert ist
        df_master = df_master.drop(columns=['Raender'])

        # Neue Spalte: plot_label generieren
        df_master.insert(2, 'plot_label', '')
        df_master['plot_label'] = (
                df_master['Statisches System'].astype(str) + "_" +
                df_master['section_type'].astype(str) + "_" +
                df_master['Bodenaufbau'].astype(str)
        )

        # Neue Spalte: Gesamte Querschnittshöhe (h_tot) berechnen
        df_master.insert(21, 'h_tot [m]', df_master['h_QS [m]'] + df_master['h_Bodenaufbau [m]'])

        # Einheitenanpassung: Lasten von [N/m2] in [kN/m2] konvertieren
        df_master['Last Struktur [kN/m2]'] = df_master.pop('Last Struktur [N/m2]') / 1000
        df_master['Last Bodenaufbau [kN/m2]'] = df_master.pop('Last Bodenaufbau [N/m2]') / 1000

        # Neue Spalte: Gesamte Last berechnen
        df_master['Last_tot [kN/m2]'] = df_master['Last Struktur [kN/m2]'] + df_master['Last Bodenaufbau [kN/m2]']

        # Zeitstempel generieren
        timestamp = datetime.now().strftime("%y%m%d_%H%M")

        final_output_file = f"{timestamp}_Members.xlsx"
        df_master.to_excel(final_output_file, index=False)

        print(f"Master-Datenbank erfolgreich gespeichert unter: {final_output_file}")

        print("\n==================================================")
        print(f"DONE! Master-Datenbank erfolgreich erstellt.")
        print(f"Datei: {final_output_file}")
        print(f"Spaltenanzahl: {df_master.shape[1]} | Zeilenanzahl gesamt: {df_master.shape[0]}")
        print("==================================================")
    else:
        print("\nAbbruch: Keine bereinigten Daten zum Zusammenführen vorhanden.")