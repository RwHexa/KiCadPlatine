# -*- coding: utf-8 -*-
"""
make_trafo_footprint.py  --  erzeugt Platine7812.pretty/Trafo_Print_15VA_4pin.kicad_mod
========================================================================================
WARUM ein eigener Footprint?
Der KiCad-Footprint Transformer_THT:Transformer_37x44 legt in beiden Pin-Reihen
je 6 Kupferpads auf 5,08-mm-Raster an, nummeriert aber nur 4 davon (1/2 primaer,
3/4 sekundaer). Die 8 uebrigen Pads haengen an keinem Netz: sie erzeugen beim
Routen DRC-Kollisionen und waeren auf der fertigen Platine blanke Kupferinseln
-- auf der Primaerseite neben 230 V~ unerwuenscht.

Dieses Skript kopiert den Original-Footprint (Umriss, Courtyard, Bemassung bleiben
erhalten) und wirft die unnummerierten Pads heraus.

Geometrie (vom Original uebernommen):
  Koerper    37 x 44 mm
  Pad 1 / 2  (primaer)   x = 0 / 20,32 mm,  y = 0
  Pad 3 / 4  (sekundaer) x = 5,08 / -5,08 mm, y = 25,4 mm
  -> Reihenabstand 25,4 mm = Kriechstrecke zwischen Primaer und Sekundaer

>>> PRUEFEN: Rastermass und Pinbelegung gegen das Datenblatt des tatsaechlich
>>> beschafften Printtrafos abgleichen (15 VA, 230 V / 15 V). Weichen sie ab,
>>> hier die Pad-Koordinaten anpassen und das Skript erneut laufen lassen.

Ausfuehren mit:  python make_trafo_footprint.py
"""
import os
from kiutils.footprint import Footprint

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = (r"C:\Program Files\KiCad\8.0\share\kicad\footprints"
        r"\Transformer_THT.pretty\Transformer_37x44.kicad_mod")
LIB  = os.path.join(HERE, "Platine7812.pretty")
NAME = "Trafo_Print_15VA_4pin"

os.makedirs(LIB, exist_ok=True)

fp = Footprint.from_file(SRC)
before = len(fp.pads)
fp.pads = [p for p in fp.pads if p.number.strip()]
after = len(fp.pads)

fp.entryName = NAME
fp.libraryNickname = "Platine7812"
fp.description = ("Printtrafo 15 VA, 230 V / 15 V, Koerper 37x44 mm, 4 Pins "
                  "(1/2 primaer, 3/4 sekundaer, Reihenabstand 25,4 mm). "
                  "Abgeleitet von Transformer_THT:Transformer_37x44, ohne dessen "
                  "unnummerierte Pads. Masse am realen Trafo pruefen!")
fp.tags = "transformer mains 15VA 230V 15V THT"

out = os.path.join(LIB, NAME + ".kicad_mod")
fp.to_file(out)
print("OK -> %s" % out)
print("Pads: %d -> %d  (%d unnummerierte entfernt)" % (before, after, before - after))
print("Verbleibend:", [(p.number, round(p.position.X, 2), round(p.position.Y, 2))
                       for p in fp.pads])

# ---- fp-lib-table schreiben, damit KiCad die Projektbibliothek findet ---------
tbl = os.path.join(HERE, "fp-lib-table")
if not os.path.exists(tbl):
    with open(tbl, "w", encoding="utf-8") as f:
        f.write("(fp_lib_table\n"
                '  (lib (name "Platine7812")(type "KiCad")'
                '(uri "${KIPRJMOD}/Platine7812.pretty")(options "")(descr "Projekt-Footprints"))\n'
                ")\n")
    print("fp-lib-table angelegt ->", tbl)
else:
    print("fp-lib-table existiert bereits.")
