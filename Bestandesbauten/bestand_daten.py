# -*- coding: utf-8 -*-
"""
Datengrundlage der Bestandesanalyse Wohnbauten.

Alle Werte sind von Hand aus den Planunterlagen gelesen oder aus dem Inventar
251217_Inventar.xlsx bzw. der Auswertung 251204_Auswertung.xlsx uebernommen.
Jede Zeile nennt ihre Quelle. Nichts in dieser Datei ist gerechnet; die
Berechnung steht in bestand_auswertung.py.

Data Validation (wie im bestehenden Inventar):
    0 = keine verwertbare Grundlage
    1 = Annahme, aus Architekturplaenen oder Plausibilitaet abgeleitet
    2 = belegt, aus Ingenieurplaenen oder angeschriebener Masskette

Spannweitenregel (festgelegt am 06.11.2026):
    einachsig gespannt          -> Achsmass in Tragrichtung
    zweiachsig, linienfoermig   -> kuerzere Spannweite des massgebenden Feldes
    punktgestuetzte Flachdecke  -> groessere Rasterachse
    Decke ueber UG wird gesondert gefuehrt, nicht im Hauptdatensatz
"""

# ======================================================================================================================
# KENNWERTE DER BAUSTOFFE
# ======================================================================================================================
# Quelle: database_261106.db, Tabelle products. EPD-Mittelwerte = arithmetisches Mittel aller gueltigen EPD einer
# Festigkeitsklasse (ValidEPD = 1, Man_Ausschluss = 1), gleiche Auswahl wie opt_and_plot.get_mean_materials.
BAUSTOFFE = {
    # Schluessel: (GWP [kg CO2-eq/kg], Rohdichte [kg/m3], Beschrieb, Quelle)
    "beton_epd_C30_37": (0.08831, 2378.0, "Beton C30/37, Mittel aus 23 EPD",
                         "database_261106.db, products, MECH_PROP = C30/37, ValidEPD = 1"),
    "beton_kbob":       (0.101,   2300.0, "Hochbaubeton KBOB (ohne Bewehrung)",
                         "KBOB 2022 V9.0, ID 01.002"),
    "bewehrung_epd":    (0.54802, 7850.0, "Betonstahl B500B, Mittel aus 11 EPD",
                         "database_261106.db, products, MATERIAL = Steel_reinforcing_bar, MECH_PROP = B500B"),
    "bewehrung_kbob":   (0.785,   7850.0, "Armierungsstahl KBOB",
                         "KBOB 2022 V9.0, ID 06.003"),
    "vollholz_epd":     (0.13362,  474.3, "Konstruktionsvollholz, Mittel aus 3 EPD",
                         "database_261106.db, products, MATERIAL = Solid_structural_timber, ValidEPD = 1"),
    "vollholz_kbob":    (0.129,    485.0, "Massivholz Fichte/Tanne/Laerche, luftgetrocknet, rau",
                         "KBOB 2022 V9.0, ID 07.001"),
    "brettstapel_kbob": (0.1884,   450.0, "Brettstapel Strattura, Produktion Schweiz",
                         "KBOB 2022 V9.0, ID 07.002.02"),
}

# Zwei Annahmen zum Betonausstoss, wie am 06.11.2026 festgelegt:
#   "heute" = EPD-Mittelwert C30/37 (vergleichbar mit den Kurven des Deckenrechners)
#   "alt"   = KBOB Hochbaubeton 101 kg CO2-eq/t (hoeherer Wert, wie in 251204_Auswertung verwendet)
BETON_VARIANTEN = {"heute": "beton_epd_C30_37", "alt": "beton_kbob"}
STAHL_VARIANTEN = {"heute": "bewehrung_epd", "alt": "bewehrung_kbob"}
HOLZ_VARIANTEN = {"heute": "vollholz_epd", "alt": "vollholz_kbob"}

# ----------------------------------------------------------------------------------------------------------------------
# Zuordnung der KBOB-Bezeichnungen aus 251204_Auswertung zu den tragenden Baustoffen oben.
# Alle uebrigen Schichten werden mit dem KBOB-Wert V9.0 gerechnet, in beiden Varianten gleich.
TRAGENDE_STOFFE = {
    "Hochbaubeton (ohne Bewehrung)": "beton",
    "Armierungsstahl": "bewehrung",
    "Massivholz Fichte / Tanne / Lärche, luftgetrocknet, rau": "vollholz",
    "Massivholz Fichte / Tanne / Lärche, luftgetrocknet, rau, Produktion Schweiz": "vollholz",
}
VARIANTEN = {
    "beton": BETON_VARIANTEN,
    "bewehrung": STAHL_VARIANTEN,
    "vollholz": HOLZ_VARIANTEN,
}

# ----------------------------------------------------------------------------------------------------------------------
# Korrekturen an Eingabewerten aus 251204_Auswertung.xlsx.
# Das Quell-Excel wird nicht veraendert; die Korrektur wirkt nur in dieser Auswertung und wird im Excel ausgewiesen.
KORREKTUREN = {
    # (Objekt, Schicht-Nr.): (Feld, neuer Wert, Begruendung)
    ("Regina_Solitaer", 2): ("anteil", 0.012739,
                             "In 251204_Auswertung steht 0.0012739 (10 kg/m3). Alle uebrigen Objekte liegen bei "
                             "96...100 kg/m3; der Wert ist um den Faktor 10 zu klein. Korrigiert auf 100 kg/m3 "
                             "(Festlegung 06.11.2026)."),
    ("Regina_Zeile1-2", 2): ("anteil", 0.012739,
                             "Gleicher Faktor-10-Fehler wie beim Solitaer, gleich korrigiert."),
}

# ======================================================================================================================
# OBJEKTE (ein Datensatz je Objekt und Deckentyp)
# ======================================================================================================================
# lx, ly: Achsmasse des massgebenden Deckenfeldes [m]; l_massg: Wert nach der Spannweitenregel
OBJEKTE = [
 dict(id="ABZ_Dietlikon", objekt="Dietlikon", portfolio="ABZ", nutzung="Wohnen", baujahr=1970,
      deckentyp="Stahlbeton-Vollplatte", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=4.05, ly=5.77, l_massg=4.05, regel="kuerzere Spannweite",
      h_tragend_mm=200, bewehrung_vol=0.012229,
      dv=1,
      quelle_spannweite="ABZ/Dietlikon/Plaene 1_50/Haus A+B 2.-7. Obergeschoss.pdf, S. 1, M 1:50",
      beleg="DIE_AB_detail",
      quelle_aufbau="251204_Auswertung.xlsx, Blatt Bodenaufbauten (Angaben Bauabteilung ABZ, Mail F. Stutz 16.09.2025)",
      bemerkung="Lichte Raumbreite 3.85 m zwischen Durisolwand 25 cm und Innenwand 15 cm, Achsmass 4.05 m. "
                "Ob die 15 cm-Innenwaende tragend sind, ist aus dem Architekturplan nicht belegt."),

 dict(id="Entlisberg_2", objekt="Entlisberg 2", portfolio="ABZ", nutzung="Wohnen", baujahr=2017,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=4.70, ly=6.26, l_massg=6.26, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=280, bewehrung_vol=0.012739,
      dv=2,
      quelle_spannweite="251217_Inventar.xlsx, Blatt ABZ: 6.26 m in 2 Richtungen, 4.70 m in 1 Richtung",
      beleg="ENT_GA_1OG",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitte inkl. Bodenaufbau, Gebaeude A, Aufbau B.01)",
      bemerkung="Zwei Feldtypen: quadratisches Feld 6.26 x 6.26 m und einachsiges Feld 4.70 m. "
                "Massgebend ist das groessere Feld."),

 dict(id="Glattpark", objekt="Glattpark", portfolio="ABZ", nutzung="Wohnen", baujahr=2018,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=5.805, ly=7.225, l_massg=5.805, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=280, bewehrung_vol=0.012739,
      dv=2,
      quelle_spannweite="ABZ/Glattpark/6.23 Architekt/Rev Werkplaene 1 zu 50 Nordareal/Grundrisse/AN/"
                        "53-AR-AN-GA-GR-O2-WER-0105-_.pdf, S. 1, M 1:50, Masskette Achsen 1...5 und A...D",
      beleg="GLA_chain, GLA_vchain",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitte, Bereich Wohnen/Zimmer)",
      bemerkung="Achsraster quer 7.22 / 4.04 / 6.65 m, laengs 5.23 / 4.41 / 5.81 m (A...D total 15.44 m). "
                "Groesstes Feld 7.22 x 5.81 m."),

 dict(id="Herrlig_Holzdecke", objekt="Herrlig", portfolio="ABZ", nutzung="Wohnen", baujahr=1948,
      deckentyp="Holzbalkendecke 12/22, a = 0.65 m", system="einachsig, einfach gelagert",
      lx=3.61, ly=5.49, l_massg=3.61, regel="Achsmass in Tragrichtung",
      h_tragend_mm=220, bewehrung_vol=0.0,
      dv=1,
      quelle_spannweite="ABZ/Herrlig/3500_Plan_GR_SCHN_Block_1-3.pdf, S. 1, M 1:100, Gebaeudetiefe 9.79 m",
      beleg="HER_chain, HER_vchain",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Bestand)",
      bemerkung="Gebaeudetiefe 9.79 m, durch eine Laengswand in Baender von 3.61 m und 5.49 m geteilt. "
                "Die Spannrichtung der Balken ist in den Planunterlagen nicht angeschrieben. Angenommen "
                "wird das kuerzere Band, weil 12/22 bei a = 0.65 m ueber 5.49 m nicht tragfaehig waere "
                "(l/h = 25). Diese Annahme ist nicht aus den Plaenen belegt."),

 dict(id="Regina_Zeile1-2", objekt="Regina Kaegi Hof, Zeile 1 und 2", portfolio="ABZ", nutzung="Wohnen", baujahr=2001,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=4.05, ly=5.04, l_massg=4.05, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=200, bewehrung_vol=0.012739,
      dv=1,
      quelle_spannweite="ABZ/Regina Kaegi Hof/6000_2001_Rev. Plan_2.-4. OG Solitaer_2.-5. OG Zeilen.pdf, S. 1, "
                        "Masskette Achsen 1...10",
      beleg="REG_Z2_detail",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitt)",
      bemerkung="Achsraster quer 4.05 / 3.60 m, Gebaeudetiefe 10.00 m, durch eine Laengswand in zwei Felder "
                "von rund 5.04 m geteilt. Bewehrungsgehalt in 251204_Auswertung mit 0.00127 angesetzt "
                "(10 kg/m3) - offensichtlich ein Faktor-10-Fehler, hier auf 100 kg/m3 korrigiert."),

 dict(id="Regina_Solitaer", objekt="Regina Kaegi Hof, Solitaer", portfolio="ABZ", nutzung="Wohnen", baujahr=2001,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=None, ly=None, l_massg=None, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=220, bewehrung_vol=0.012739,
      dv=1,
      quelle_spannweite=None,
      beleg="REG_OG",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitt)",
      bemerkung="Runder Solitaerbau, eigener Grundriss auf demselben Plan. Die Spannweiten des Solitaers "
                "habe ich noch nicht abgelesen; der Schichtaufbau (220 mm Beton) ist aus 251204_Auswertung "
                "uebernommen."),

 dict(id="Ruggaechern_H21", objekt="Ruggaechern H21", portfolio="ABZ", nutzung="Wohnen", baujahr=2007,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=4.69, ly=6.00, l_massg=4.69, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=240, bewehrung_vol=0.012739,
      dv=1,
      quelle_spannweite="251217_Inventar.xlsx, Blatt ABZ: minimale Spannweite 3.02 m, maximale 4.69 m und 6.00 m",
      beleg=None,
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitt)",
      bemerkung="Spannweiten aus dem Inventar uebernommen. Welche Werte zu welchem Feld gehoeren, ist dort "
                "nicht festgehalten; die Zuordnung 4.69 x 6.00 m ist eine Annahme und in der zweiten Runde "
                "an den Plaenen zu pruefen."),

 dict(id="Sihlfeld", objekt="Sihlfeld", portfolio="ABZ", nutzung="Wohnen", baujahr=1928,
      deckentyp="Holzbalkendecke mit Ueberbeton (Ertuechtigung 2012)", system="einachsig, einfach gelagert",
      lx=4.18, ly=None, l_massg=4.18, regel="Achsmass in Tragrichtung",
      h_tragend_mm=205, bewehrung_vol=0.0,
      dv=1,
      quelle_spannweite="ABZ/Sihlfeld/6.23 Architekt/7_001_4_Index4 1OG.pdf, S. 1, M 1:50",
      beleg="SIH_ARCH_1OG",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Umbau, Ing.)",
      bemerkung="Lichte Raummasse 3.29...4.18 m. Die Planlegende bestaetigt die Deckentypen "
                "(Bestand Hourdisdecke, Neubau Betonflachdecke, je Decke ueber EG). Die Spannrichtung der "
                "Holzbalken ist nicht angeschrieben."),

 dict(id="Toblerstrasse", objekt="Toblerstrasse", portfolio="ABZ", nutzung="Wohnen", baujahr=2018,
      deckentyp="Stahlbeton-Flachdecke", system="zweiachsig, linienfoermig gelagert, durchlaufend",
      lx=4.86, ly=6.68, l_massg=4.86, regel="kuerzere Spannweite des groessten Feldes",
      h_tragend_mm=280, bewehrung_vol=0.012739,
      dv=1,
      quelle_spannweite="ABZ/Toblerstrasse/6.23 Architekt/2500_20171106_NB_H9_3_Grundriss.pdf, S. 1, M 1:50",
      beleg="TOB_H9_3OG",
      quelle_aufbau="251204_Auswertung.xlsx (Plaene Arch., Schnitt)",
      bemerkung="Polygonaler Grundriss, Deckenfelder nicht rechteckig. Lichte Raummasse zwischen tragenden "
                "Betonwaenden 25 cm: 4.56...6.68 m. Fuer Toblerstrasse liegen keine Ingenieurplaene vor, "
                "die Zuordnung der tragenden Waende ist eine Interpretation des Architekturplans."),

 dict(id="Ottostrasse_Holzdecke", objekt="Ottostrasse", portfolio="ABZ", nutzung="Wohnen", baujahr=1927,
      deckentyp="Holzbalkendecke", system="einachsig, einfach gelagert",
      lx=5.00, ly=None, l_massg=5.00, regel="Achsmass in Tragrichtung",
      h_tragend_mm=None, bewehrung_vol=0.0,
      dv=1,
      quelle_spannweite="ABZ/Ottostrasse/6.25 Bauingenieur/1800_20160429_IS_Beilage Schematischer Grundriss "
                        "der tragenden Waenden.pdf, S. 1, M 1:105.3",
      beleg="OTT_ING",
      quelle_aufbau=None,
      bemerkung="Schematischer Grundriss der Erdbebenueberpruefung: Gebaeude rund 40 x 10.2 m, eine "
                "durchlaufende Laengswand in der Mitte, Baender von je rund 5.0 m. Kein Schichtaufbau in "
                "251204_Auswertung erfasst, deshalb noch keine GWP-Berechnung moeglich."),

 dict(id="Kanzlei", objekt="Kanzlei", portfolio="ABZ", nutzung="Wohnen", baujahr=1930,
      deckentyp="Stahlbeton-Flachdecke (Annahme)", system=None,
      lx=None, ly=None, l_massg=None, regel=None,
      h_tragend_mm=None, bewehrung_vol=None,
      dv=0,
      quelle_spannweite=None, beleg=None, quelle_aufbau=None,
      bemerkung="Laut Inventar nur unvermasste Architekturplaene von 1973 ohne erkennbare Materialisierung. "
                "Keine Spannweite und kein Aufbau ableitbar."),

 dict(id="Wiedikon", objekt="Wiedikon", portfolio="ABZ", nutzung="Wohnen", baujahr=1975,
      deckentyp="Hourdisdecke (Annahme)", system=None,
      lx=None, ly=None, l_massg=None, regel=None,
      h_tragend_mm=340, bewehrung_vol=None,
      dv=0,
      quelle_spannweite=None, beleg=None, quelle_aufbau=None,
      bemerkung="Rueckmeldung ABZ (Mail F. Stutz 16.09.2025): keine Plaene vorhanden. Die Decke der "
                "Einstellhalle wurde sondiert (26 cm Stahltonelemente, 8 cm Ueberzugsbeton); dass die "
                "Geschossdecken gleich ausgefuehrt sind, ist eine Vermutung der Bauherrschaft."),

 dict(id="dsp_Alterszentrum", objekt="Alterszentrum Abegg-Huus", portfolio="dsp", nutzung="Wohnen", baujahr=2016,
      deckentyp="Stahlbeton-Flachdecke", system="punktgestuetzt",
      lx=None, ly=None, l_massg=None, regel="groessere Rasterachse",
      h_tragend_mm=260, bewehrung_vol=None,
      dv=1,
      quelle_spannweite="dsp/Alterszentrum, Abegg-Huus/14729_Strukturplaene.pdf, S. 5 (Strukturplan 2. OG), M 1:200",
      beleg="ALT_2OG",
      quelle_aufbau=None,
      bemerkung="Strukturplan belegt Decke h = 26 cm, Stuetzen rechteckig 40x20 cm und rund d = 25/30 cm, "
                "Betonwaende 18...25 cm. Der Grundriss ist polygonal und im Massstab 1:200 nicht bemasst; "
                "eine belastbare Rasterweite konnte ich daraus nicht ablesen. Kein Schichtaufbau erfasst."),

 dict(id="dsp_KernSued", objekt="Kern Sued", portfolio="dsp", nutzung="Wohnen, Buero", baujahr=2014,
      deckentyp="Stahlbeton-Flachdecke", system="punktgestuetzt",
      lx=None, ly=None, l_massg=None, regel="groessere Rasterachse",
      h_tragend_mm=260, bewehrung_vol=None,
      dv=1,
      quelle_spannweite="dsp/Kern Sued/Tragstruktur Regelgeschoss.pdf, S. 1, M 1:300",
      beleg="KER_block",
      quelle_aufbau=None,
      bemerkung="Plan belegt Decke d = 26 cm, Stuetzen 25/25 cm, Fassadenpfeiler 20 cm, Kerne 25 cm. "
                "Im Massstab 1:300 ohne Masskette; aus der Geometrie geschaetzte Querspannweiten 5.0...5.9 m, "
                "nicht belegt. Kein Schichtaufbau erfasst."),

 dict(id="dsp_Lagerplatz", objekt="Lagerplatz", portfolio="dsp", nutzung="Wohnen, Buero, Schule", baujahr=2016,
      deckentyp="Holz-Beton-Verbunddecke auf Unterzuegen", system="einachsig, durchlaufend",
      lx=6.05, ly=None, l_massg=6.05, regel="Achsmass in Tragrichtung",
      h_tragend_mm=280, bewehrung_vol=None,
      dv=1,
      quelle_spannweite="dsp/Lagerplatz/141_B_S_01-05_M20_32_V Verbunddecke Referenzgeschoss.pdf, S. 1, "
                        "Grundriss 2. OG M 1:200",
      beleg="LAG_chain, LAG_legend",
      quelle_aufbau=None,
      bemerkung="Plan belegt: Verbunddecke 16 cm Brettstapel + 12 cm Beton C30/37 = 28 cm, Unterzug "
                "b = 40 cm, h = 0.15 m unter der Platte, Stuetzen 25x25 cm, Bruestung b = 0.25 m, "
                "h = 1.20 m. Masskette im Grundriss: 7.40 / 11.30 / 6.04 m im Kopfbau, 7.75 / 5.40 / "
                "5.55 / 6.05 m im Regelbereich. Welcher dieser Werte die Spannweite der Verbunddecke ist "
                "und welcher die Spannweite der Unterzuege, geht aus dem Plan 1:200 nicht hervor; "
                "angesetzt ist der groesste Wert des Regelbereichs. Kein Schichtaufbau erfasst."),
]

# ======================================================================================================================
# HINWEISE ZU EINGABEWERTEN AUS 251204_Auswertung.xlsx, die nicht korrigiert wurden
# ======================================================================================================================
HINWEISE = [
    ("Sihlfeld",
     "Der Bewehrungsgehalt der Ueberbetonschicht ist in 251204_Auswertung mit einem Volumenanteil von "
     "0.0764 angesetzt, das entspricht 600 kg/m3. Alle uebrigen Objekte liegen bei 96...100 kg/m3. "
     "Der Wert sieht nach demselben Faktor-10-Fehler aus wie bei Regina Kaegi Hof, ist aber nicht "
     "bestaetigt; er wurde deshalb unveraendert uebernommen. Mit 60 kg/m3 waeren es rund 4.5 statt "
     "44.7 kg CO2-eq/m2 fuer die Bewehrung."),
    ("Ottostrasse, Kanzlei, Wiedikon, Alterszentrum, Kern Sued, Lagerplatz",
     "Fuer diese Objekte ist in 251204_Auswertung kein Schichtaufbau erfasst. Ohne Aufbau laesst sich "
     "kein GWP rechnen; die Zeilen bleiben in den GWP-Spalten leer."),
    ("Wiedikon",
     "Die Deckenstaerke 340 mm stammt aus der Sondierung der Einstellhalle (26 cm Stahltonelemente, "
     "8 cm Ueberzugsbeton). Eine Hourdisdecke ist keine Vollplatte; mit dieser Staerke als Vollquerschnitt "
     "zu rechnen waere falsch."),
]

# ======================================================================================================================
# DECKEN UEBER UNTERGESCHOSS (gesondert gefuehrt, nicht im Hauptdatensatz)
# ======================================================================================================================
DECKEN_UEBER_UG = [
 dict(id="Glattpark_UG", objekt="Glattpark", h_tragend_mm="300...600",
      quelle="251217_Inventar.xlsx, Blatt ABZ: Decken ue. UG 30-60 cm Beton",
      bemerkung="Abfangungen ueber Tiefgarage, nicht mit den Regelgeschossen vergleichbar."),
 dict(id="Regina_UG", objekt="Regina Kaegi Hof", h_tragend_mm="200...400",
      quelle="251217_Inventar.xlsx, Blatt ABZ: Zeilen Decke ue. UG 40-20 cm Beton, 17 cm Aufboden",
      bemerkung="Abfangungen ueber Tiefgarage."),
 dict(id="Dietlikon_UG", objekt="Dietlikon", h_tragend_mm=None,
      quelle="251217_Inventar.xlsx, Blatt ABZ",
      bemerkung="UG mit Kellerabteilen und Stuetzen, Abfangdecke; Tiefgarage separat."),
]
