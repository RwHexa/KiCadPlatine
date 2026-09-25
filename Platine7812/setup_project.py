# -*- coding: utf-8 -*-
"""
setup_project.py  --  traegt Netzklassen und Entwurfsregeln in Platine7812.kicad_pro ein
=========================================================================================
WICHTIG: kicad-cli (und KiCad selbst) schreiben die .kicad_pro beim Beenden neu und
normalisieren sie dabei -- eigene Netzklassen gehen dabei verloren. Dieses Skript
patcht die vorhandene Projektdatei nachtraeglich und ist idempotent: es laesst alles
Unbekannte stehen und setzt nur die eigenen Eintraege.

Es muss deshalb IMMER ALS LETZTER SCHRITT laufen (siehe build_all.py).

Eingetragen werden:
  * Netzklasse "Netzspannung" (2,0 mm Bahnbreite, 2,5 mm Abstand) fuer /L, /L_F, /N
  * sinnvolle Vorgabe-Bahnbreiten und Via-Groessen
Die eigentliche Isolationsregel (6,4 mm Primaer gegen Sekundaer) steht in
Platine7812.kicad_dru -- die Datei wird von KiCad nicht angetastet.

Ausfuehren mit:  python setup_project.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRO  = os.path.join(HERE, "Platine7812.kicad_pro")

HV_CLASS = {
    "bus_width": 12,
    "clearance": 2.5,
    "diff_pair_gap": 0.25,
    "diff_pair_via_gap": 0.25,
    "diff_pair_width": 0.2,
    "line_style": 0,
    "microvia_diameter": 0.3,
    "microvia_drill": 0.1,
    "name": "Netzspannung",
    "pcb_color": "rgba(200, 52, 52, 1.000)",
    "schematic_color": "rgba(200, 52, 52, 1.000)",
    "track_width": 2.0,
    "via_diameter": 1.2,
    "via_drill": 0.6,
    "wire_width": 6,
}

HV_NETS = ["/L", "/L_F", "/N"]

with open(PRO, encoding="utf-8") as f:
    pro = json.load(f)

ns = pro.setdefault("net_settings", {})
classes = ns.setdefault("classes", [])

# Default-Klasse auf projekttaugliche Werte heben
for c in classes:
    if c.get("name") == "Default":
        c["clearance"] = 0.25
        c["track_width"] = 1.5
        c["via_diameter"] = 1.2
        c["via_drill"] = 0.6

# Netzspannungsklasse setzen bzw. auffrischen
classes = [c for c in classes if c.get("name") != "Netzspannung"] + [HV_CLASS]
ns["classes"] = classes

ns["netclass_patterns"] = [{"netclass": "Netzspannung", "pattern": n} for n in HV_NETS]

# Auswahllisten fuer Bahnbreiten / Vias
bds = pro.setdefault("board", {}).setdefault("design_settings", {})
bds["track_widths"] = [0.0, 0.5, 1.0, 1.5, 2.0]
bds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0},
                         {"diameter": 1.2, "drill": 0.6}]
bds.setdefault("rules", {})["min_clearance"] = 0.2
bds["rules"]["min_track_width"] = 0.25

with open(PRO, "w", encoding="utf-8") as f:
    json.dump(pro, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("OK -> %s" % PRO)
print("Netzklassen:", [(c["name"], c["clearance"], c["track_width"]) for c in ns["classes"]])
print("Netzspannung gilt fuer:", ", ".join(HV_NETS))
