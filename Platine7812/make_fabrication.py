# -*- coding: utf-8 -*-
"""
make_fabrication.py  --  erzeugt die Fertigungsdaten fuer Platine7812
======================================================================
Legt den Ordner "fertigung" an mit:
  * Gerber-Dateien aller benoetigten Lagen
  * Excellon-Bohrdateien (.drl)  <-- muessen SEPARAT erzeugt werden;
       "Plot"/"export gerbers" allein liefert sie NICHT. Ein ZIP ohne .drl
       ist beim Fertiger unbrauchbar.
  * Platine7812_Fertigung.zip  (das, was man dem Fertiger schickt)
  * Stueckliste (BOM) als CSV
  * Schaltplan und Bestueckungsplan als PDF

Vorbedingung: Platine7812.kicad_pcb muss aktuell sein (build_all.py) und die
Massflaeche muss gefuellt sein -- das Skript prueft das und warnt sonst.

Ausfuehren mit:  python make_fabrication.py
"""
import os
import glob
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
KBIN = r"C:\Program Files\KiCad\8.0\bin"
CLI  = os.path.join(KBIN, "kicad-cli.exe")
KPY  = os.path.join(KBIN, "python.exe")
PCB  = os.path.join(HERE, "Platine7812.kicad_pcb")
SCH  = os.path.join(HERE, "Platine7812.kicad_sch")
OUT  = os.path.join(HERE, "fertigung")

# Lagen, die der Fertiger braucht (Courtyard/Fab sind reine Doku und bleiben draussen)
LAYERS = "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"


def run(label, cmd):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("FEHLER bei %s:\n%s\n%s" % (label, r.stdout, r.stderr))
        sys.exit(1)
    print("  %s: ok" % label)


# ---- Vorbedingung: ist die Massflaeche gefuellt? ------------------------------
check = subprocess.run(
    [KPY, "-c",
     "import pcbnew,sys;b=pcbnew.LoadBoard(r'%s');"
     "z=list(b.Zones());"
     "print('FILLED' if z and all(x.IsFilled() for x in z) else 'EMPTY')" % PCB],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
if "EMPTY" in (check.stdout or ""):
    print("WARNUNG: Die Massflaeche ist NICHT gefuellt -- sie fehlt dann in den")
    print("         Gerber-Dateien. Erst 'python build_all.py' laufen lassen")
    print("         (oder in KiCad die Taste B druecken und speichern).")
    sys.exit(1)
print("Massflaeche ist gefuellt.")

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

print("\nErzeuge Fertigungsdaten ...")
run("Gerber",        [CLI, "pcb", "export", "gerbers", "--layers", LAYERS,
                      "--no-protel-ext", "-o", OUT + os.sep, PCB])
# Bohrdateien: eigener Aufruf, sonst fehlen sie!
run("Bohrdateien",   [CLI, "pcb", "export", "drill", "--format", "excellon",
                      "--drill-origin", "absolute", "--excellon-units", "mm",
                      "--generate-map", "--map-format", "pdf",
                      "-o", OUT + os.sep, PCB])
run("Stueckliste",   [CLI, "sch", "export", "bom",
                      "--fields", "Reference,Value,Footprint,${QUANTITY}",
                      "--group-by", "Value,Footprint",
                      "-o", os.path.join(OUT, "Platine7812_BOM.csv"), SCH])
run("Schaltplan-PDF", [CLI, "sch", "export", "pdf",
                       "-o", os.path.join(OUT, "Platine7812_Schaltplan.pdf"), SCH])
run("Bestueckungsplan", [CLI, "pcb", "export", "pdf", "--include-border-title",
                         "--layers", "F.Silkscreen,F.Fab,Edge.Cuts",
                         "-o", os.path.join(OUT, "Platine7812_Bestueckung.pdf"), PCB])

# ---- ZIP fuer den Fertiger ----------------------------------------------------
zip_path = os.path.join(OUT, "Platine7812_Fertigung.zip")
gerbers = sorted(glob.glob(os.path.join(OUT, "*.gbr")))
drills  = sorted(glob.glob(os.path.join(OUT, "*.drl")))

if not drills:
    print("\nABBRUCH: keine .drl-Bohrdatei erzeugt -- ohne sie ist das ZIP unbrauchbar.")
    sys.exit(1)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in gerbers + drills:
        z.write(f, os.path.basename(f))

print("\nZIP fuer den Fertiger: %s" % zip_path)
print("  %d Gerber-Lagen + %d Bohrdatei(en):" % (len(gerbers), len(drills)))
for f in gerbers + drills:
    print("    %s" % os.path.basename(f))
print("\nAusserdem in %s:" % OUT)
print("  Platine7812_BOM.csv           Stueckliste")
print("  Platine7812_Schaltplan.pdf    Schaltplan")
print("  Platine7812_Bestueckung.pdf   Bestueckungsplan")
