# -*- coding: utf-8 -*-
"""
build_all.py  --  erzeugt das komplette Projekt Platine7812 aus den Skripten
============================================================================
Reihenfolge (die Reihenfolge ist wichtig!):

  1. make_trafo_footprint.py   eigener Trafo-Footprint + fp-lib-table
  2. build_schematic.py        Schaltplan  -> Platine7812.kicad_sch
  3. kicad-cli sch erc         Schaltplanpruefung
  4. kicad-cli sch export      Netzliste   -> Platine7812.net
  5. build_pcb.py              Leiterplatte-> Platine7812.kicad_pcb  (KiCad-Python!)
  6. setup_project.py          Netzklassen -> Platine7812.kicad_pro  (MUSS zuletzt,
                               weil kicad-cli die .kicad_pro sonst wieder normalisiert)
  7. kicad-cli pcb drc         Designregelpruefung

Ausfuehren mit der System-Python:   python build_all.py
(Die Schritte rufen die jeweils passende Python selbst auf.)
"""
import os
import subprocess
import sys

HERE     = os.path.dirname(os.path.abspath(__file__))
KICAD    = r"C:\Program Files\KiCad\8.0\bin"
KICAD_PY = os.path.join(KICAD, "python.exe")
KICAD_CLI = os.path.join(KICAD, "kicad-cli.exe")
SCH      = os.path.join(HERE, "Platine7812.kicad_sch")
PCB      = os.path.join(HERE, "Platine7812.kicad_pcb")
NET      = os.path.join(HERE, "Platine7812.net")

STEPS = [
    ("Trafo-Footprint",  [sys.executable, os.path.join(HERE, "make_trafo_footprint.py")]),
    ("Schaltplan",       [sys.executable, os.path.join(HERE, "build_schematic.py")]),
    ("ERC",              [KICAD_CLI, "sch", "erc", "--severity-all",
                          "-o", os.path.join(HERE, "erc.rpt"), SCH]),
    ("Netzliste",        [KICAD_CLI, "sch", "export", "netlist",
                          "--format", "kicadsexpr", "-o", NET, SCH]),
    ("Leiterplatte",     [KICAD_PY, "-u", os.path.join(HERE, "build_pcb.py")]),
    ("Netzklassen",      [sys.executable, os.path.join(HERE, "setup_project.py")]),
    ("DRC",              [KICAD_CLI, "pcb", "drc", "--severity-all",
                          "-o", os.path.join(HERE, "drc.rpt"), PCB]),
]

failed = []
for name, cmd in STEPS:
    print("\n" + "=" * 70)
    print(">>> %s" % name)
    print("=" * 70)
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    # SKiDL/kiutils-Warnungen zu fehlenden KICAD*_SYMBOL_DIR ausblenden
    for line in out.splitlines():
        if line.startswith("WARNING: KICAD"):
            continue
        print(line)
    if r.returncode != 0:
        failed.append("%s (Exitcode %d)" % (name, r.returncode))

print("\n" + "=" * 70)
if failed:
    print("FEHLGESCHLAGEN:", "; ".join(failed))
    sys.exit(1)
print("Alle Schritte durchgelaufen. Berichte: erc.rpt, drc.rpt")
