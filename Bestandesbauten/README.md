# Bestandesanalyse Wohnbauten

Analyse der Geschossdecken des Gebäudeportfolios (ABZ, dsp) und Vergleich mit den Kurven
des Deckenrechners.

## Dateien

| Datei | Inhalt |
|---|---|
| `bestand_daten.py` | Objekte, Spannweiten, statische Systeme, Quellen, Kennwerte der Baustoffe. Von Hand gepflegt. |
| `bestand_auswertung.py` | Erzeugt `<Datum>_Bestandesanalyse_Wohnbauten.xlsx` aus `bestand_daten.py`, den Schichtaufbauten in `251204_Auswertung.xlsx` und der KBOB-Liste V9.0. |
| `bestand_belege.py` | Erzeugt `<Datum>_Quellenbeleg_Spannweiten.pdf`: je abgelesenem Wert ein markierter Planausschnitt mit Dateiname, Seite und Massstab. |
| `bestand_plots.py` | Erzeugt die Diagramme GWP über Spannweite mit Kurven, Streuband und Punktwolke der Bestandesbauten. |

## Ablauf

```bash
# 1 Kurven rechnen (dauert lange, aus dem Ordner Workflow/ starten)
cd ../Workflow
../.venv/bin/python 261111_Run_Kurven_1D.py
../.venv/bin/python 261111_Run_Kurven_2D.py

# 2 Bestandes-Excel erzeugen
cd ../Bestandesbauten
../.venv/bin/python bestand_auswertung.py

# 3 Quellenbeleg erzeugen
../.venv/bin/python bestand_belege.py

# 4 Diagramme erzeugen
../.venv/bin/python bestand_plots.py
```

Schritt 2 bis 4 laufen unabhängig von Schritt 1; nur `bestand_plots.py` braucht die
Batch-Ergebnisse aus `Workflow/Results/`.

## Festlegungen

- Bezugsgrösse 1 m² Deckenfläche, nur die Decke, ohne Stützen und Wände
- Indikator: Treibhausgasemissionen total (Herstellung + Entsorgung), ohne Transport, ohne Amortisation
- Nichttragende Schichten: KBOB 2022, Version 9.0
- Tragende Schichten in zwei Varianten: EPD-Mittelwert C30/37 («heute») und KBOB Hochbaubeton 101 kg CO₂-eq/t («alt»)
- Spannweite: einachsig → Achsmass in Tragrichtung; zweiachsig linienförmig → kürzere Spannweite
  des massgebenden Feldes; punktgestützt → grössere Rasterachse
- Decken über UG werden gesondert geführt

Die offenen Punkte stehen im Blatt «Offene Punkte» des Excels.
