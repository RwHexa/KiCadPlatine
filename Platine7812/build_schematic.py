"""
build_schematic.py  --  erzeugt Platine7812.kicad_sch (KiCad 8)
================================================================
Einfaches Netzteil 230 V~ -> +12 V DC mit Festspannungsregler 7812,
nach dem Referenzbild (TR1 - Brueckengleichrichter 4x 1N4007 - C1/C2 -
LM7812 - C3/C4 - JP1/JP2).

Methode (bewaehrt aus PlatineNetzOB2263): jedes Bauteil wird bei Rotation 0
platziert; jeder Pin bekommt einen kurzen Stub + ein lokales Netz-Label.
Gleiche Label-Namen auf demselben Blatt sind elektrisch verbunden
-> rasterbuendige, robuste Konnektivitaet ohne Draht-Routing.

Regeneriere mit:  python build_schematic.py
"""
import uuid, math, os
from copy import deepcopy
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.common import (Position, Property, Effects, Stroke, Font,
                                  Justify, TitleBlock)
from kiutils.items.schitems import (SchematicSymbol, Connection, LocalLabel,
                                    SymbolProjectInstance, SymbolProjectPath, Text)

HERE   = os.path.dirname(os.path.abspath(__file__))
SYMDIR = r"C:\Program Files\KiCad\8.0\share\kicad\symbols"
PROJ   = "Platine7812"
OUT    = os.path.join(HERE, PROJ + ".kicad_sch")
GRID   = 1.27                       # KiCad-Verbindungsraster
STUB   = 2.54

# ---- Auslegung (hier aendern, dann Skript neu laufen lassen) ------------------
# Sekundaerspannung 15 V~ (nicht 18 V~ wie im Referenztext als Beispiel genannt):
#   15 V~ -> Scheitel 21,2 V - 1,4 V (2 Dioden) = 19,8 V, abzgl. Brumm ~2 V
#   -> ca. 17,8 V am 7812-Eingang. Dropout des 7812 = 2 V -> 14 V noetig: erfuellt.
#   Verlustleistung: (17,8 V - 12 V) * 0,5 A = 2,9 W  (bei 18 V~ waeren es 5,5 W!)
U_SEC   = "15V"
I_OUT   = "0,5A"
# Trafo 15 VA, nicht 10 VA: bei Gleichrichtung mit Ladeelko fliesst der Strom in
# kurzen Spitzen, der Trafo-Effektivstrom ist rund 1,6...1,8 mal der Gleichstrom.
# 0,5 A DC -> ca. 0,85 A eff. Ein 10-VA-Typ liefert bei 15 V nur 0,67 A und waere
# damit ueberlastet; 15 VA / 15 V = 1,0 A reicht mit Reserve.
TRAFO_VA = "15VA"
C1_VAL  = "2200uF/35V"              # Ladeelko: I*t/dU = 0,5A*10ms/2,3V ~ 2200uF
F1_VAL  = "T 160mA / 250V"          # prim. 15VA/230V = 65mA, traege ~2x -> 160mA


def U():
    return str(uuid.uuid4())


def snap(v):
    return round(v / GRID) * GRID


def J(h):
    return Justify(horizontally=h) if h else Justify()


# ---- Symbolbibliotheken laden -------------------------------------------------
libs = {}
for nick, fn in [("Device", "Device.kicad_sym"),
                 ("Connector", "Connector.kicad_sym"),
                 ("Regulator_Linear", "Regulator_Linear.kicad_sym"),
                 ("power", "power.kicad_sym")]:
    lib = SymbolLib.from_file(os.path.join(SYMDIR, fn))
    libs[nick] = {s.entryName: s for s in lib.symbols}


def libsym(nick, name):
    """Liefert eine Kopie des Symbols. Abgeleitete Symbole (extends, z.B.
    LM7812_TO220 -> LM7805_TO220) werden flachgeklopft: Grafik/Pins der Basis
    uebernehmen und die Unit-Namen auf den neuen Symbolnamen umschreiben --
    sonst zeichnet Eeschema ein leeres Kaestchen ohne Pins."""
    s = deepcopy(libs[nick][name])
    if s.extends:
        base = deepcopy(libs[nick][s.extends])
        units = base.units
        for un in units:
            un.entryName = un.entryName.replace(base.entryName, name, 1)
        s.units          = units
        s.graphicItems   = base.graphicItems
        s.pins           = base.pins
        s.pinNames       = base.pinNames
        s.pinNamesHide   = base.pinNamesHide
        s.pinNamesOffset = base.pinNamesOffset
        s.hidePinNumbers = base.hidePinNumbers
        s.extends        = None
    s.libraryNickname = nick
    return s


# ---- leeres v8-Schaltplangeruest ---------------------------------------------
sch = Schematic.create_new()
sch.uuid = U()
sch.paper.paperSize = "A4"
sch.filePath = OUT
ROOTPATH = "/" + sch.uuid

_embedded = set()


def embed(nick, name):
    lid = f"{nick}:{name}"
    if lid not in _embedded:
        sch.libSymbols.append(libsym(nick, name))
        _embedded.add(lid)


# ---- Platzierung + Verdrahtung -----------------------------------------------
def place(ref, nick, name, value, fp, px, py, pinmap, yoff=8.89, hideval=False):
    px, py = snap(px), snap(py)
    embed(nick, name)
    s = libsym(nick, name)
    ss = SchematicSymbol(libraryNickname=nick, entryName=name,
                         position=Position(px, py, 0), unit=1,
                         inBom=True, onBoard=True, dnp=False, uuid=U())
    ss.properties = [
        Property(key="Reference", value=ref, id=0,
                 position=Position(px, snap(py - yoff), 0),
                 effects=Effects(font=Font(height=1.27, width=1.27))),
        Property(key="Value", value=value, id=1,
                 position=Position(px, snap(py + yoff), 0),
                 effects=Effects(font=Font(height=1.0, width=1.0), hide=hideval)),
        Property(key="Footprint", value=fp, id=2, position=Position(px, py, 0),
                 effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
        Property(key="Datasheet", value="~", id=3, position=Position(px, py, 0),
                 effects=Effects(font=Font(height=1.27, width=1.27), hide=True)),
    ]
    ss.instances = [SymbolProjectInstance(
        name=PROJ,
        paths=[SymbolProjectPath(sheetInstancePath=ROOTPATH, reference=ref, unit=1)])]
    sch.schematicSymbols.append(ss)

    pins = {p.number: p for un in s.units for p in un.pins}
    for num, net in pinmap.items():
        p = pins[num]
        ex, ey = snap(px + p.position.X), snap(py - p.position.Y)   # v8: Y gespiegelt
        ang = p.position.angle
        ox, oy = -math.cos(math.radians(ang)), math.sin(math.radians(ang))
        sx, sy = snap(ex + ox * STUB), snap(ey + oy * STUB)
        sch.graphicalItems.append(Connection(points=[Position(ex, ey), Position(sx, sy)],
                                             stroke=Stroke(width=0), uuid=U()))
        if net is None:            # Power-/Flag-Symbol: Stub, aber kein Label
            continue
        just = "left" if ox > 0.3 else ("right" if ox < -0.3 else None)
        sch.labels.append(LocalLabel(text=net, position=Position(sx, sy, 0),
                                     effects=Effects(font=Font(height=1.27, width=1.27),
                                                     justify=J(just)),
                                     uuid=U()))


def note(txt, x, y, size=1.27, bold=False):
    sch.texts.append(Text(text=txt, position=Position(snap(x), snap(y), 0),
                          effects=Effects(font=Font(height=size, width=size, bold=bold),
                                          justify=J("left")),
                          uuid=U()))


FP = {
    # Netzklemme mit 10 mm Raster: 5,08 mm waeren fuer 230 V~ zu eng
    "TERM2": "TerminalBlock_RND:TerminalBlock_RND_205-00023_1x02_P10.00mm_Horizontal",
    "FUSE":  "Fuse:Fuseholder_Clip-5x20mm_Littelfuse_111_Inline_P20.00x5.00mm_D1.05mm_Horizontal",
    "TRAFO": "Platine7812:Trafo_Print_15VA_4pin",   # eigener FP, siehe make_trafo_footprint.py
    "DO41":  "Diode_THT:D_DO-41_SOD81_P7.62mm_Horizontal",
    "CP16":  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm",
    "CP10":  "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "CRECT": "Capacitor_THT:C_Rect_L7.0mm_W2.5mm_P5.00mm",
    "TO220": "Package_TO_SOT_THT:TO-220-3_Vertical",
    "PIN1":  "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
}

# ------------------------------------------------------------------ Ueberschriften
note("PRIMAERSEITE  --  230 V~  --  LEBENSGEFAHR", 20, 24, 2.0, True)
note("SEKUNDAERSEITE  --  SELV", 150, 24, 2.0, True)
note("Gleichrichtung", 120, 40, 1.5, True)
note("Siebung", 162, 40, 1.5, True)
note("Festspannungsregler", 196, 40, 1.5, True)
note("ISOLATIONSBARRIERE (Kriechstrecke >= 6,4 mm)", 100, 172, 1.3, False)

# ------------------------------------------------------------------ PRIMAER (230 V~)
place("J1", "Connector", "Screw_Terminal_01x02", "230V~ L/N", FP["TERM2"],
      30, 95, {"1": "L", "2": "N"})
place("F1", "Device", "Fuse", F1_VAL, FP["FUSE"],
      52, 87, {"1": "L", "2": "L_F"})
place("TR1", "Device", "Transformer_1P_1S", "230V/" + U_SEC + " " + TRAFO_VA, FP["TRAFO"],
      88, 95, {"1": "L_F", "2": "N", "3": "AC2", "4": "AC1"}, yoff=13.97)

# ------------------------------------------------------------------ Brueckengleichrichter
# Device:D  ->  Pin 1 = K (Kathode), Pin 2 = A (Anode)
place("D1", "Device", "D", "1N4007", FP["DO41"], 126, 70,  {"1": "VRAW", "2": "AC1"})
place("D2", "Device", "D", "1N4007", FP["DO41"], 126, 84,  {"1": "VRAW", "2": "AC2"})
place("D3", "Device", "D", "1N4007", FP["DO41"], 126, 112, {"1": "AC1", "2": "GND"})
place("D4", "Device", "D", "1N4007", FP["DO41"], 126, 126, {"1": "AC2", "2": "GND"})

# ------------------------------------------------------------------ Siebung vor dem Regler
place("C1", "Device", "C_Polarized", C1_VAL, FP["CP16"], 165, 95, {"1": "VRAW", "2": "GND"})
place("C2", "Device", "C", "100nF/100V", FP["CRECT"],    182, 95, {"1": "VRAW", "2": "GND"})

# ------------------------------------------------------------------ Regler
# Regulator_Linear:LM7812_TO220 -> Pin 1 = VI, Pin 2 = GND, Pin 3 = VO
place("U1", "Regulator_Linear", "LM7812_TO220", "LM7812", FP["TO220"],
      210, 88, {"1": "VRAW", "2": "GND", "3": "V12"}, yoff=11.43)

# ------------------------------------------------------------------ Siebung nach dem Regler
place("C3", "Device", "C", "100nF/50V", FP["CRECT"],          238, 95, {"1": "V12", "2": "GND"})
place("C4", "Device", "C_Polarized", "100uF/25V", FP["CP10"], 255, 95, {"1": "V12", "2": "GND"})

# ------------------------------------------------------------------ Ausgang
place("JP1", "Connector", "Conn_01x01_Pin", "DC OUT z.B. +12V", FP["PIN1"],
      272, 76, {"1": "V12"})
place("JP2", "Connector", "Conn_01x01_Pin", "0V = GND", FP["PIN1"],
      272, 114, {"1": "GND"})

# ------------------------------------------------------------------ Power-Symbole (ERC)
# Das Label wird von place() ans Stub-Ende gesetzt -- Pin-Winkel beachten:
# power:GND zeigt nach unten (270 deg), power:PWR_FLAG nach oben (90 deg).
place("#GND1", "power", "GND", "GND", "", 200, 140, {"1": "GND"}, hideval=True)

# PWR_FLAG: sagt dem ERC, dass diese Netze gespeist werden (sonst "kein Treiber")
for i, (net, x) in enumerate([("GND", 170), ("VRAW", 152), ("L", 44), ("N", 62)]):
    place("#FLG" + str(i + 1), "power", "PWR_FLAG", "PWR_FLAG", "", x, 152,
          {"1": net}, hideval=True)

# ------------------------------------------------------------------ Titelblock
sch.titleBlock = TitleBlock()
sch.titleBlock.title = "Netzteil 230 V~ -> +12 V DC / " + I_OUT + " (7812)"
sch.titleBlock.company = "RwTec"
sch.titleBlock.revision = "A"
sch.titleBlock.date = "2026-09-25"
sch.titleBlock.comments = {1: "Erzeugt mit build_schematic.py aus dem Referenz-Schaltbild"}

sch.to_file()
print("OK ->", OUT)
print("Bauteile:", len(sch.schematicSymbols), " Labels:", len(sch.labels))
