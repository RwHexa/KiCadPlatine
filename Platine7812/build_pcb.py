# -*- coding: utf-8 -*-
"""
build_pcb.py  --  erzeugt Platine7812.kicad_pcb aus Platine7812.net
===================================================================
Baut die Leiterplatte vollstaendig aus der Netzliste auf: laedt jeden
Footprint, platziert ihn, legt die Netze an, weist sie den Pads zu,
routet und fuellt die Massflaeche. Die Netzliste (und damit der
Schaltplan) ist die einzige Quelle der Wahrheit -- ein manueller
"Netzliste importieren"-Schritt in KiCad entfaellt.

Aufbau (2 Lagen, THT):
  PRIMAERSEITE  oben  (y < 86): J1 - F1 - TR1-Primaer, 230 V~
  ISOLATIONSBARRIERE y = 86, der Trafo ueberbrueckt sie bauartbedingt
  SEKUNDAERSEITE unten (y > 90): Brueckengleichrichter - C1/C2 - U1 - C3/C4 - JP1/JP2
  GND: Massflaeche auf B.Cu, bewusst NUR auf der Sekundaerseite
       (keine Massflaeche unter den netzspannungsfuehrenden Bahnen!)

Kreuzungsfreie Brueckenanordnung: D1 und D4 sind um 180 Grad gedreht.
Dadurch liegen die beiden Kathoden (VRAW) innen nebeneinander und die
beiden GND-Anoden ebenfalls -- die Bruecke selbst braucht keine Kreuzung:
      AC1 --|<|-- VRAW   VRAW --|<|-- AC2     (obere Reihe: D1 gedreht, D2)
      AC1 --|<|-- GND    GND  --|<|-- AC2     (untere Reihe: D3, D4 gedreht)
Nur VRAW muss die AC2-Bahn queren -- das erledigen zwei Durchkontaktierungen.

Ausfuehren MIT DER KICAD-PYTHON (nicht der System-Python):
  "C:\\Program Files\\KiCad\\8.0\\bin\\python.exe" build_pcb.py
"""
import os
import re
import pcbnew

HERE  = os.path.dirname(os.path.abspath(__file__))
PROJ  = "Platine7812"
NET   = os.path.join(HERE, PROJ + ".net")
PCB   = os.path.join(HERE, PROJ + ".kicad_pcb")
FPDIR = r"C:\Program Files\KiCad\8.0\share\kicad\footprints"

# ---- Platzierung: ref -> (x_mm, y_mm, rot_deg) --------------------------------
# Der Anker sitzt bei diesen THT-Footprints auf Pad 1.
PLACE = {
    # ---------------- PRIMAERSEITE  230 V~  (oben) ----------------
    "J1":  (104,     68,   0),   # Netzklemme L/N, 10 mm Raster: L(104/68), N(114/68)
    "F1":  (124,     82,  90),   # Feinsicherung 5x20, hochkant (spart 16 mm Breite):
                                 #   Pad 1 = L   bei y 77/82,  Pad 2 = L_F bei y 62/67
    "TR1": (145,     64,   0),   # Printtrafo: Primaerpads y=64, Sekundaerpads y=89,4
    # ---------------- SEKUNDAERSEITE  SELV  (unten) ----------------
    # Die ganze Sekundaerseite liegt UNTER dem Trafo -- so bleibt die Platine
    # unter 100 x 100 mm (deutlich guenstigere Fertigung).
    "D1":  (112.62, 100, 180),   # Bruecke: K(VRAW) innen, A(AC1) aussen links
    "D2":  (120,    100,   0),   #          K(VRAW) innen, A(AC2) aussen rechts
    "D3":  (105,    110,   0),   #          K(AC1) aussen links, A(GND) innen
    "D4":  (127.62, 110, 180),   #          K(AC2) aussen rechts, A(GND) innen
    "C1":  (137,    106,   0),   # Ladeelko 2200uF/35V (D16)
    "C2":  (137,    120,   0),   # 100nF Folie, parallel zu C1
    "U1":  (158,    106,   0),   # LM7812 TO-220 stehend, Kuehlkoerper dahinter
    "C4":  (155,    122,   0),   # 100uF/25V am Ausgang
    "C3":  (168,    122,   0),   # 100nF Folie am Ausgang
    "JP1": (185,    104,   0),   # DC OUT +12V
    "JP2": (185,    116,   0),   # 0V = GND
}

BOARD        = (100, 55, 192, 132)   # x1, y1, x2, y2  -> 92 x 77 mm
BARRIER_Y    = 86                    # Isolationsbarriere (horizontal)
BARRIER_SEGS = [(100, 130), (175, 192)]  # Luecke: dort steht der Trafo
HEATSINK     = (151, 98, 170, 112)   # reservierte Flaeche Kuehlkoerper U1
GND_ZONE     = (102, 92, 190, 130)   # Massflaeche NUR sekundaerseitig

# Beschriftungen, die sonst auf einem Pad landen, versetzen: ref -> (x_mm, y_mm)
REF_POS = {
    "TR1": (148, 78),   # sonst genau auf Pad 1 (Anker)
}

W_HV  = 2.0     # Leiterbahnbreite netzspannungsfuehrend (L, N, L_F)
W_PWR = 1.5     # Leiterbahnbreite Sekundaerseite (bis 1 A)

# ---- Leiterbahnen: (netz, [(x, y), ...], breite, lage) ------------------------
# "F" = Oberseite (F.Cu), "B" = Rueckseite (B.Cu); Vias siehe VIAS.
TRACKS = [
    # --- Primaer 230 V~ -------------------------------------------------------
    # L: J1.1 -> unterhalb der Klemme an J1.2 (= N) vorbei -> F1 Pad 1
    ("L",    [(104, 68), (104, 76), (124, 76), (124, 77)],    W_HV,  "F"),
    ("L",    [(124, 77), (124, 82)],                          W_HV,  "F"),   # F1-Pad-Paar 1
    # L_F: F1 Pad 2 -> TR1 Pad 1
    ("L_F",  [(124, 62), (124, 67)],                          W_HV,  "F"),   # F1-Pad-Paar 2
    ("L_F",  [(124, 67), (140, 67), (145, 64)],               W_HV,  "F"),
    # N: J1.2 -> oberhalb von F1 hinweg -> TR1 Pad 2 (laeuft unter dem Trafokoerper,
    #    dort liegen keine Pads); Abstand zur L_F-Bahn: 10 mm
    ("N",    [(114, 68), (114, 57), (165.32, 57), (165.32, 64)], W_HV, "F"),

    # --- Trafo sekundaer -> Bruecke (AC1 links, AC2 rechts, kreuzungsfrei) -----
    ("AC1",  [(139.92, 89.4), (139.92, 93), (105, 93), (105, 100)], W_PWR, "F"),
    ("AC1",  [(105, 100), (105, 110)],                              W_PWR, "F"),
    ("AC2",  [(150.08, 89.4), (150.08, 96), (127.62, 96), (127.62, 100)], W_PWR, "F"),
    ("AC2",  [(127.62, 100), (127.62, 110)],                        W_PWR, "F"),

    # --- VRAW: Bruecke -> C1/C2 -> Reglereingang ------------------------------
    ("VRAW", [(112.62, 100), (120, 100)],                     W_PWR, "F"),
    # Querung der AC2-Bahn im freien Korridor zwischen den beiden Diodenreihen
    ("VRAW", [(120, 100), (122, 104)],                        W_PWR, "F"),
    ("VRAW", [(122, 104), (134, 104)],                        W_PWR, "B"),   # unter AC2 durch
    ("VRAW", [(134, 104), (137, 106)],                        W_PWR, "F"),
    ("VRAW", [(137, 106), (137, 120)],                        W_PWR, "F"),   # -> C2
    # an C1.2 (GND, bei 144,5/106) vorbei zum Reglereingang
    ("VRAW", [(137, 106), (139, 102), (155, 102), (158, 106)], W_PWR, "F"),

    # --- V12: Reglerausgang -> C3/C4 -> Klemme --------------------------------
    ("V12",  [(163.08, 106), (175, 106), (185, 104)],         W_PWR, "F"),   # -> JP1
    ("V12",  [(163.08, 106), (163.08, 112)],                  W_PWR, "F"),   # Stamm nach unten
    ("V12",  [(163.08, 112), (150, 112), (150, 122), (155, 122)], W_PWR, "F"),  # -> C4
    ("V12",  [(163.08, 112), (168, 117), (168, 122)],         W_PWR, "F"),   # -> C3

    # --- GND: komplett auf der Rueckseite, daher kreuzungsfrei zu F.Cu --------
    # (THT-Pads sind durchkontaktiert, B.Cu-Bahnen koennen direkt anschliessen)
    ("GND",  [(112.62, 110), (120, 110)],                     W_PWR, "B"),
    ("GND",  [(120, 110), (125, 115), (142, 115), (142, 120)], W_PWR, "B"),  # -> C2.2
    ("GND",  [(142, 120), (144.5, 116), (144.5, 106)],        W_PWR, "B"),   # -> C1.2
    # GND muss um U1.1 (= VRAW) und U1.3 (= V12) herum -> U1.2 von unten anfahren
    ("GND",  [(144.5, 106), (148, 111), (160.54, 111), (160.54, 106)], W_PWR, "B"),
    ("GND",  [(160.54, 111), (160, 116), (160, 122)],         W_PWR, "B"),   # -> C4.2
    # an C3.1 (= V12, bei 168/122) vorbei zu C3.2
    ("GND",  [(160, 122), (163, 126), (174, 126), (173, 122)], W_PWR, "B"),
    ("GND",  [(173, 122), (178, 122), (185, 116)],            W_PWR, "B"),   # -> JP2
]

# Durchkontaktierungen: (netz, x, y)
VIAS = [("VRAW", 122, 104), ("VRAW", 134, 104)]


def V(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def read_netlist(path):
    """-> comps {ref: (value, 'Lib:Footprint')},  nets {netname: [(ref, pad), ...]}"""
    t = open(path, encoding="utf-8").read()
    comps = {}
    for m in re.finditer(
            r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', t):
        comps[m.group(1)] = (m.group(2), m.group(3))
    nets = {}
    seg = t[t.find("(nets"):]
    for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)((?:\s*\(node [^\n]*)+)', seg):
        nets[m.group(1)] = re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2))
    return comps, nets


def main():
    comps, nets = read_netlist(NET)
    print("Netzliste: %d Bauteile, %d Netze" % (len(comps), len(nets)))

    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(2)

    # ---- Netze anlegen ---------------------------------------------------------
    netinfo = {}
    for name in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni

    def net(short):
        """'AC1' -> NETINFO_ITEM, egal ob das Netz '/AC1' oder 'AC1' heisst."""
        for cand in ("/" + short, short):
            if cand in netinfo:
                return netinfo[cand]
        raise KeyError("Netz nicht gefunden: " + short)

    # ---- Footprints laden, platzieren, Pads mit Netzen verbinden ---------------
    pad2net = {}
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad2net[(ref, pad)] = name

    placed, missing, unconnected = 0, [], []
    for ref, (value, fpid) in sorted(comps.items()):
        lib, fpname = fpid.split(":", 1)
        # Projekteigene Bibliothek zuerst, sonst die KiCad-Standardbibliotheken
        libdir = os.path.join(HERE, lib + ".pretty")
        if not os.path.isdir(libdir):
            libdir = os.path.join(FPDIR, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libdir, fpname)
        if fp is None:
            missing.append("%s (%s)" % (ref, fpid))
            continue
        fp.SetReference(ref)
        fp.SetValue(value)
        x, y, rot = PLACE[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        if ref in REF_POS:
            rx, ry = REF_POS[ref]
            fp.Reference().SetPosition(V(rx, ry))
        board.Add(fp)
        placed += 1
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad2net:
                pad.SetNet(netinfo[pad2net[key]])
            else:
                unconnected.append("%s.%s" % key)

    # ---- Leiterbahnen ----------------------------------------------------------
    layers = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    ntracks = 0
    for nname, pts, width, lay in TRACKS:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(V(x1, y1))
            t.SetEnd(V(x2, y2))
            t.SetWidth(pcbnew.FromMM(width))
            t.SetLayer(layers[lay])
            t.SetNet(net(nname))
            board.Add(t)
            ntracks += 1

    for nname, x, y in VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y))
        v.SetDrill(pcbnew.FromMM(0.6))
        v.SetWidth(pcbnew.FromMM(1.2))
        v.SetNet(net(nname))
        board.Add(v)

    # ---- Grafik: Platinenumriss, Barriere, Beschriftung ------------------------
    def seg(x1, y1, x2, y2, layer, w):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(x1, y1))
        s.SetEnd(V(x2, y2))
        s.SetLayer(layer)
        s.SetWidth(pcbnew.FromMM(w))
        board.Add(s)

    def rect(x1, y1, x2, y2, layer, w):
        for a in [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]:
            seg(a[0], a[1], a[2], a[3], layer, w)

    def text(txt, x, y, size=2.0, rot=0, layer=None):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetPosition(V(x, y))
        t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(size / 7.0))
        t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        board.Add(t)

    rect(BOARD[0], BOARD[1], BOARD[2], BOARD[3], pcbnew.Edge_Cuts, 0.15)
    for xa, xb in BARRIER_SEGS:
        seg(xa, BARRIER_Y, xb, BARRIER_Y, pcbnew.Dwgs_User, 0.4)
    rect(HEATSINK[0], HEATSINK[1], HEATSINK[2], HEATSINK[3], pcbnew.Dwgs_User, 0.2)

    # Text muss links vom Trafo-Bestueckungsdruck bleiben (beginnt bei x = 130,9)
    text("230V~ LEBENSGEFAHR", 102, 79.5, 1.0)
    text("SEKUNDAER +12V SELV", 102, 88.5, 1.3)
    text("ISOLATION >= 6,4 mm", 102, 84.5, 1.3, 0, pcbnew.Dwgs_User)
    text("KUEHLKOERPER", 152, 96.5, 1.2, 0, pcbnew.Dwgs_User)
    text("Netzteil 7812  -  RwTec  -  Rev A", 102, 129, 1.4)

    # ---- Massflaeche (nur Sekundaerseite!) -------------------------------------
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(net("GND"))
    zone.SetLocalClearance(pcbnew.FromMM(0.3))
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetIsFilled(True)
    zx1, zy1, zx2, zy2 = GND_ZONE
    poly = pcbnew.SHAPE_POLY_SET()
    poly.NewOutline()
    for px, py in [(zx1, zy1), (zx2, zy1), (zx2, zy2), (zx1, zy2)]:
        poly.Append(pcbnew.FromMM(px), pcbnew.FromMM(py))
    zone.SetOutline(poly)
    board.Add(zone)

    # ---- Selbsttest: ueberlappende Abstandsflaechen (Courtyards) ---------------
    boxes = []
    for f in board.GetFootprints():
        bb = f.GetCourtyard(pcbnew.F_Cu).BBox()
        boxes.append((f.GetReference(),
                      pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
                      pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())))
    clashes = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, c = boxes[i], boxes[j]
            if a[1] < c[2] and c[1] < a[2] and a[3] < c[4] and c[3] < a[4]:
                clashes.append("%s <-> %s" % (a[0], c[0]))

    pcbnew.SaveBoard(PCB, board)

    # ---- Massflaeche fuellen ---------------------------------------------------
    # ZONE_FILLER stuerzt auf einem frisch erzeugten Board ab (Segfault). Auf einem
    # GELADENEN Board mit aufgebauter Konnektivitaet laeuft er dagegen sauber durch,
    # deshalb hier der Umweg ueber Speichern -> Laden -> Fuellen -> Speichern.
    # Ohne diesen Schritt bliebe die Flaeche in den Gerber-Dateien leer!
    b2 = pcbnew.LoadBoard(PCB)
    b2.BuildConnectivity()
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    filled = [z.IsFilled() for z in b2.Zones()]
    pcbnew.SaveBoard(PCB, b2)

    print("Massflaeche gefuellt:", all(filled) and len(filled) > 0)
    print("Platziert: %d Footprints, %d Leiterbahnsegmente, %d Vias"
          % (placed, ntracks, len(VIAS)))
    if missing:
        print("FEHLENDE FOOTPRINTS:", missing)
    if unconnected:
        print("Pads ohne Netz:", unconnected)
    print("Courtyards:", ", ".join(clashes) if clashes else "keine Kollisionen.")
    print("Board gespeichert ->", PCB)


main()
