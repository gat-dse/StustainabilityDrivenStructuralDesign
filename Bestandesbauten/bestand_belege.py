# -*- coding: utf-8 -*-
"""
Erzeugt das Quellen-PDF der Bestandesanalyse: je abgelesenem Wert ein Planausschnitt mit
Markierung, Dateiname, Seitenzahl und Massstab.

Die Ausschnitte werden mit pdftoppm direkt aus den Originalplaenen gerendert; es wird nichts
zwischengespeichert und keine Plandatei veraendert.

Voraussetzung: poppler-utils (pdftoppm) im Pfad, Pakete pillow und reportlab.
"""

import os
import subprocess
import sys
import tempfile
from datetime import date

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

PLAN_ORDNER_KANDIDATEN = [
    os.path.expanduser("~/Documents/04 Working Folder/ETH Nachhaltigkeit im Bau/"
                       "21_Analyse typischer Tragwerke/01_Daten und Pläne"),
    os.path.expanduser("~/mnt/21_Analyse typischer Tragwerke/01_Daten und Pläne"),
]

# ----------------------------------------------------------------------------------------------------------------------
# BELEGE
# crop: (Seite, dpi, x, y, Breite, Hoehe) in Pixeln der mit diesem dpi gerenderten Seite
# marker: Liste von (x, y, Breite, Hoehe) relativ zum Ausschnitt; markiert die abgelesene Stelle
BELEGE = [
 dict(objekt="Dietlikon", pdf="ABZ/Dietlikon/Pläne 1_50/Haus A+B     2.-7. Obergeschoss.pdf",
      crop=(1, 150, 180, 1670, 1300, 1750), marker=[(300, 1140, 420, 90), (300, 240, 420, 90)],
      massstab="1:50", jahr="1968",
      abgelesen="Lichte Raumbreite 3.85 m zwischen Durisol-Aussenwand 25 cm und Innenwand 15 cm, "
                "Raumtiefe 5.57 m. Achsmass der kurzen Richtung 4.05 m.",
      verwendet="massgebende Spannweite 4.05 m"),

 dict(objekt="Glattpark", pdf="ABZ/Glattpark/6.23 Architekt/Rev Werkpläne 1 zu 50 Nordareal/Grundrisse/AN/"
                              "53-AR-AN-GA-GR-O2-WER-0105-_.pdf",
      crop=(1, 150, 400, 230, 2400, 420), marker=[(0, 155, 2400, 50)],
      massstab="1:50", jahr="2017",
      abgelesen="Masskette der Achsen 1...4: 7.22 m, 4.04 m, 6.65 m.",
      verwendet="längere Rasterachse des massgebenden Feldes 7.22 m"),

 dict(objekt="Glattpark", pdf="ABZ/Glattpark/6.23 Architekt/Rev Werkpläne 1 zu 50 Nordareal/Grundrisse/AN/"
                              "53-AR-AN-GA-GR-O2-WER-0105-_.pdf",
      crop=(1, 150, 180, 450, 500, 2200), marker=[(60, 100, 120, 2000)],
      massstab="1:50", jahr="2017",
      abgelesen="Masskette der Achsen A...D: 5.23 m, 4.41 m, total 15.44 m, unteres Feld 5.81 m.",
      verwendet="kürzere Spannweite des massgebenden Feldes 5.81 m"),

 dict(objekt="Regina Kägi Hof, Zeile 2",
      pdf="ABZ/Regina Kägi Hof/6000_2001_Rev. Plan_2.-4. OG Solitär_2.-5. OG Zeilen.pdf",
      crop=(1, 150, 2075, 280, 2300, 1150), marker=[(0, 0, 2300, 70), (0, 380, 2300, 60)],
      massstab="1:100", jahr="2001",
      abgelesen="Achsraster quer 4.05 / 3.60 / 3.60 / 3.60 / 4.05 m, Gebäudetiefe 10.00 m, "
                "durch eine Längswand in zwei Felder von rund 5.04 m geteilt.",
      verwendet="massgebende Spannweite 4.05 m"),

 dict(objekt="Herrlig", pdf="ABZ/Herrlig/3500_Plan_GR_SCHN_Block_1-3.pdf",
      crop=(1, 180, 0, 300, 420, 1300), marker=[(90, 180, 120, 760)],
      massstab="1:100", jahr="1995 (Revisionsplan Bestand 1948)",
      abgelesen="Gebäudetiefe 9.79 m, Balkon 1.80 m. Die Längswand teilt die Tiefe in Bänder von "
                "3.61 m und 5.49 m.",
      verwendet="massgebende Spannweite 3.61 m (Spannrichtung der Balken angenommen, nicht angeschrieben)"),

 dict(objekt="Ottostrasse",
      pdf="ABZ/Ottostrasse/6.25 Bauingenieur/1800_20160429_IS_Beilage Schematischer Grundriss der tragenden Wänden.pdf",
      crop=(1, 150, 100, 200, 2300, 750), marker=[(0, 250, 2300, 100)],
      massstab="1:105.3", jahr="2016 (Erdbebenüberprüfung, Bestand 1927)",
      abgelesen="Schematischer Grundriss der tragenden Wände: Gebäude rund 40.0 x 10.2 m, eine "
                "durchlaufende Längswand in der Mitte, Bänder von je rund 5.0 m.",
      verwendet="massgebende Spannweite 5.0 m"),

 dict(objekt="Toblerstrasse", pdf="ABZ/Toblerstrasse/6.23 Architekt/2500_20171106_NB_H9_3_Grundriss.pdf",
      crop=(1, 150, 1700, 1500, 2400, 2400), marker=None,
      massstab="1:50", jahr="2017",
      abgelesen="Tragende Betonwände 25 cm, lichte Raummasse 4.56...6.68 m. Der Grundriss ist "
                "polygonal, die Deckenfelder sind nicht rechteckig.",
      verwendet="massgebende Spannweite 4.86 m (Interpretation, keine Ingenieurpläne vorhanden)"),

 dict(objekt="Sihlfeld", pdf="ABZ/Sihlfeld/6.23 Architekt/7_001_4_Index4 1OG.pdf",
      crop=(1, 120, 2550, 3400, 1500, 900), marker=None,
      massstab="1:50", jahr="2012 (Erneuerung, Bestand 1928)",
      abgelesen="Planlegende: Neubau Betonflachdecke (Decke über EG) und Bestand Hourdisdecke "
                "(Decke über EG).",
      verwendet="Bestätigung der Deckentypen"),

 dict(objekt="Alterszentrum Abegg-Huus", pdf="dsp/Alterszentrum, Abegg-Huus/14729_Strukturpläne.pdf",
      crop=(5, 150, 900, 150, 1700, 1300), marker=None,
      massstab="1:200", jahr="2016",
      abgelesen="Strukturplan 2. OG: Decke h = 26 cm, Stützen rechteckig 40x20 cm, Stützen rund "
                "d = 25 und 30 cm, Betonwände 18...25 cm.",
      verwendet="Deckenstärke 260 mm; eine Rasterweite ist im Plan nicht bemasst"),

 dict(objekt="Kern Süd", pdf="dsp/Kern Süd/Tragstruktur Regelgeschoss.pdf",
      crop=(1, 250, 1700, 250, 1000, 2100), marker=None,
      massstab="1:300", jahr="2014",
      abgelesen="Tragstruktur Regelgeschoss: Decke d = 26 cm, Stützen 25/25 cm, Fassadenpfeiler 20 cm, "
                "aussteifende Kerne 25 cm.",
      verwendet="Deckenstärke 260 mm; Spannweiten im Massstab 1:300 nicht belegbar"),

 dict(objekt="Lagerplatz",
      pdf="dsp/Lagerplatz/141_B_S_01-05_M20_32_V Verbunddecke Referenzgeschoss.pdf",
      crop=(1, 150, 60, 80, 1200, 900), marker=[(150, 100, 100, 780), (1100, 150, 100, 700)],
      massstab="1:200", jahr="2016",
      abgelesen="Grundriss 2. OG: Spannweiten der Verbunddecke zwischen den Unterzügen "
                "7.40 / 11.30 / 6.04 m im Kopfbau und 7.75 / 5.40 / 5.55 / 6.05 m im Regelbereich.",
      verwendet="massgebende Spannweite 6.05 m (grösster Wert des Regelbereichs; welcher Wert die "
                "Spannweite der Verbunddecke und welcher jene der Unterzüge ist, geht aus dem Plan nicht hervor)"),

 dict(objekt="Lagerplatz",
      pdf="dsp/Lagerplatz/14713-104 1. Obergeschoss, 2.Obergeschoss.pdf",
      crop=(1, 300, 950, 1550, 1300, 700), marker=[(190, 350, 700, 330)],
      massstab="Legende", jahr="2016",
      abgelesen="Legende: Holz-Beton-Verbunddecke, Unterzug b = 40 cm, h = 0.15 m, Brüstung "
                "b = 0.25 m, h = 1.20 m, Stützen 25x25 cm.",
      verwendet="Unterzugsgeometrie 40 x 15 cm unter der Platte"),
]


def plan_ordner():
    for p in PLAN_ORDNER_KANDIDATEN:
        if os.path.isdir(p):
            return p
    raise FileNotFoundError("Planordner nicht gefunden, geprueft:\n  " + "\n  ".join(PLAN_ORDNER_KANDIDATEN))


def rendere(pdf_pfad, crop, ziel_ohne_endung):
    seite, dpi, x, y, w, h = crop
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(seite), "-l", str(seite),
                    "-x", str(x), "-y", str(y), "-W", str(w), "-H", str(h),
                    pdf_pfad, ziel_ohne_endung], check=True)
    for endung in (f"-{seite}.png", f"-{seite:02d}.png", f"-{seite:03d}.png", ".png"):
        if os.path.isfile(ziel_ohne_endung + endung):
            return ziel_ohne_endung + endung
    raise FileNotFoundError(f"Ausschnitt nicht erzeugt: {ziel_ohne_endung}")


def markiere(bild_pfad, marker):
    if not marker:
        return bild_pfad
    bild = Image.open(bild_pfad).convert("RGB")
    zeichner = ImageDraw.Draw(bild)
    breite = max(3, int(min(bild.size) / 250))
    for (x, y, w, h) in marker:
        zeichner.rectangle([x, y, x + w, y + h], outline=(220, 0, 0), width=breite)
    bild.save(bild_pfad)
    return bild_pfad


def umbrich(text, zeichenzahl):
    worte, zeilen, aktuell = text.split(), [], ""
    for wort in worte:
        if len(aktuell) + len(wort) + 1 > zeichenzahl:
            zeilen.append(aktuell)
            aktuell = wort
        else:
            aktuell = (aktuell + " " + wort).strip()
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def main():
    ordner = plan_ordner()
    name = f"{date.today():%y%m%d}_Quellenbeleg_Spannweiten.pdf"
    ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    seite_b, seite_h = landscape(A4)
    c = canvas.Canvas(ziel, pagesize=landscape(A4))
    arbeit = tempfile.mkdtemp()

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, seite_h - 25 * mm, "Quellenbeleg der abgelesenen Spannweiten und Deckenstärken")
    c.setFont("Helvetica", 10)
    for i, zeile in enumerate([
            "Bestandesanalyse Wohnbauten, Projekt «Nachhaltigkeit im Tragwerksentwurf», kfm research group, IBK, ETH Zürich",
            f"Erstellt am {date.today():%d.%m.%Y} aus den Originalplänen in «01_Daten und Pläne».",
            "Jede Seite zeigt den Planausschnitt, aus dem der Wert gelesen wurde. Rot markiert ist die Stelle der Masskette.",
            "Die zugehörigen Zahlenwerte stehen im Blatt «Objekte» des Excels Bestandesanalyse_Wohnbauten."]):
        c.drawString(20 * mm, seite_h - (35 + i * 6) * mm, zeile)
    c.showPage()

    for nr, b in enumerate(BELEGE, start=1):
        pdf_pfad = os.path.join(ordner, b["pdf"])
        if not os.path.isfile(pdf_pfad):
            print("fehlt:", pdf_pfad)
            continue
        bild_pfad = rendere(pdf_pfad, b["crop"], os.path.join(arbeit, f"beleg_{nr:02d}"))
        markiere(bild_pfad, b.get("marker"))

        c.setFont("Helvetica-Bold", 13)
        c.drawString(15 * mm, seite_h - 15 * mm, f"{nr}. {b['objekt']}")

        text_hoehe = 34 * mm
        bild = Image.open(bild_pfad)
        max_b, max_h = seite_b - 30 * mm, seite_h - 22 * mm - text_hoehe
        faktor = min(max_b / bild.width, max_h / bild.height)
        bb, bh = bild.width * faktor, bild.height * faktor
        bild_y = text_hoehe + 4 * mm + (max_h - bh) / 2
        c.drawImage(bild_pfad, (seite_b - bb) / 2, bild_y, width=bb, height=bh)

        y = text_hoehe - 2 * mm
        c.setFont("Helvetica", 8)
        for beschriftung, inhalt in [("Datei", b["pdf"]),
                                     ("Seite, Massstab, Datum", f"Seite {b['crop'][0]}, {b['massstab']}, {b['jahr']}"),
                                     ("Abgelesen", b["abgelesen"]),
                                     ("Verwendet als", b["verwendet"])]:
            for k, zeile in enumerate(umbrich(inhalt, 128)):
                if k == 0:
                    c.setFont("Helvetica-Bold", 8)
                    c.drawString(15 * mm, y, beschriftung + ":")
                c.setFont("Helvetica", 8)
                c.drawString(62 * mm, y, zeile)
                y -= 4 * mm
            y -= 1 * mm
        c.showPage()

    c.save()
    print("geschrieben:", ziel)


if __name__ == "__main__":
    main()
