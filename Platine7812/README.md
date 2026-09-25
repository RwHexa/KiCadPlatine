# Platine7812 — einfaches Netzteil 230 V~ → +12 V DC

KiCad-8-Projekt nach dem Referenz-Schaltbild: Printtrafo **TR1** → Brücken­gleich­richter
aus **4 × 1N4007** → Siebung **C1/C2** → Festspannungsregler **LM7812** → **C3/C4** →
Ausgangsklemmen **JP1 (+12 V)** und **JP2 (0 V = GND)**.

> ⚠️ **LEBENSGEFAHR:** Die **Primärseite führt Netzspannung (230 V~)**. Primär- und
> Sekundärseite sind galvanisch getrennt (SELV am Ausgang). Aufbau, Inbetriebnahme und
> Messung nur durch qualifizierte Personen, Trenntrafo verwenden, Platine nie offen
> betreiben. Der 0-V-Anschluss wird beim Einbau ins Gehäuse mit dem Schutzkontakt verbunden.

## Stand

| Prüfung | Ergebnis |
|---|---|
| ERC (Schaltplan) | **0 Verstöße** |
| DRC (Leiterplatte) | **0 Verstöße**, **0 unverbundene Pads** |
| Kriechstrecke Primär↔Sekundär | **≥ 6,4 mm**, per eigener DRC-Regel nachgerechnet |
| Platinengröße | **92,2 × 77,2 mm**, 2 Lagen, THT |

Die Platine ist **vollständig geroutet** (50 Leiterbahnsegmente, 2 Durchkontaktierungen)
und hat eine gefüllte Massefläche auf der Rückseite — ausschließlich auf der
Sekundärseite, damit unter den netzspannungsführenden Bahnen kein Kupfer liegt.

## Stückliste

| Ref | Wert | Bauform / Footprint |
|---|---|---|
| TR1 | 230 V / 15 V, **15 VA** | Printtrafo, Körper 37 × 44 mm, 4 Pins |
| F1 | **T 160 mA / 250 V** | Feinsicherung 5 × 20 mm mit Printhalter, hochkant |
| J1 | Netzeingang L/N | Schraubklemme, **10 mm Raster** |
| D1–D4 | 1N4007 | DO-41, liegend, Raster 7,62 mm |
| C1 | 2200 µF / 35 V | Elko radial, Ø 16 mm, Raster 7,5 mm |
| C2 | 100 nF / 100 V | Folie, Raster 5 mm |
| U1 | **LM7812** | TO-220 stehend, **Kühlkörper erforderlich** |
| C3 | 100 nF / 50 V | Folie, Raster 5 mm |
| C4 | 100 µF / 25 V | Elko radial, Ø 10 mm, Raster 5 mm |
| JP1 / JP2 | +12 V / 0 V | je 1 Stift, Raster 2,54 mm |

## Auslegung — warum diese Werte

**Sekundärspannung 15 V~ (nicht 18 V~).** Der Text zum Referenzbild nennt 18 V als
Beispiel. 15 V reichen aber und halbieren fast die Verlustwärme:

```
15 V~ → Scheitelwert      15 · √2        = 21,2 V
        − 2 Diodenflussspannungen (2 · 0,7 V) = 19,8 V
        − Brummspannung  ΔU = I·t/C = 0,5 A · 10 ms / 2200 µF = 2,3 V
        → Minimum am Reglereingang            ≈ 17,5 V
```

Der 7812 braucht mindestens 14 V am Eingang (12 V + 2 V Dropout) — **3,5 V Reserve**.
Verlustleistung am Regler: `(18,6 V − 12 V) · 0,5 A ≈ 3,3 W`.
Mit 18 V~ wären es **5,5 W** gewesen.

**Kühlkörper ist Pflicht.** Bei 3,3 W und 40 °C Umgebung wird ein Kühlkörper mit
**≤ 15 K/W** gebraucht (Sperrschicht bleibt dann bei rund 105 °C). Auf der Platine ist
dafür eine Fläche von **19 × 14 mm** hinter U1 freigehalten und auf der Lage `Dwgs.User`
markiert. Ohne Kühlkörper schaltet der 7812 thermisch ab.

**Trafo 15 VA, nicht 10 VA.** Bei Gleichrichtung mit Ladeelko fließt der Strom in kurzen
Spitzen; der Trafo-Effektivstrom ist rund **1,6…1,8 × der Gleichstrom**. Für 0,5 A DC sind
das ca. 0,85 A — ein 10-VA-Typ liefert bei 15 V nur 0,67 A und wäre überlastet.
15 VA / 15 V = 1,0 A reicht mit Reserve.

**Sicherung.** Primär-Nennstrom `15 VA / 230 V = 65 mA`, träge Sicherung mit etwa dem
doppelten Wert → **T 160 mA**.

## Aufbau der Leiterplatte

**Primärseite oben** (y < 86 mm): J1 → F1 → TR1-Primärwicklung.
**Sekundärseite unten** (y > 90 mm): Brücke → C1/C2 → U1 → C3/C4 → JP1/JP2.
Dazwischen liegt die **Isolationsbarriere**; sie ist auf `Dwgs.User` eingezeichnet und
wird bauartbedingt nur vom Trafo selbst überbrückt (Pin-Reihenabstand 25,4 mm).

**Kreuzungsfreie Brückenanordnung.** D1 und D4 sind um 180° gedreht. Dadurch liegen die
beiden Kathoden (VRAW) innen nebeneinander und die beiden GND-Anoden ebenfalls:

```
AC1 --|<|-- VRAW   VRAW --|<|-- AC2     obere Reihe (D1 gedreht, D2)
AC1 --|<|-- GND    GND  --|<|-- AC2     untere Reihe (D3, D4 gedreht)
```

Die Brücke selbst braucht damit keine einzige Kreuzung. Nur VRAW muss die AC2-Bahn
queren — das erledigen zwei Durchkontaktierungen im freien Korridor zwischen den
Diodenreihen. GND läuft komplett auf der Rückseite und kann deshalb nichts kreuzen.

## Dateien

| Datei | Inhalt |
|---|---|
| `Platine7812.kicad_sch` | Schaltplan |
| `Platine7812.kicad_pcb` | Leiterplatte, geroutet |
| `Platine7812.kicad_pro` | Projektdatei inkl. Netzklassen |
| `Platine7812.kicad_dru` | **eigene DRC-Regel: 6,4 mm Primär ↔ Sekundär** |
| `Platine7812.net` | Netzliste (aus dem Schaltplan erzeugt) |
| `Platine7812.pretty/` | projekteigener Trafo-Footprint |
| `fertigung/` | Gerber, Bohrdateien, ZIP, Stückliste, PDFs |
| `erc.rpt`, `drc.rpt` | Prüfberichte |

### Generatorskripte

Das Projekt wird **vollständig aus Skripten erzeugt**; die Netzliste ist die einzige
Quelle der Wahrheit für die Leiterplatte (kein manueller Netzlisten-Import nötig).

```bash
python build_all.py
```

Das durchläuft der Reihe nach:

| Schritt | Skript | Ergebnis |
|---|---|---|
| 1 | `make_trafo_footprint.py` | Trafo-Footprint + `fp-lib-table` |
| 2 | `build_schematic.py` | `.kicad_sch` |
| 3 | `kicad-cli sch erc` | `erc.rpt` |
| 4 | `kicad-cli sch export netlist` | `.net` |
| 5 | `build_pcb.py` | `.kicad_pcb` (platziert, geroutet, Zone gefüllt) |
| 6 | `setup_project.py` | Netzklassen in `.kicad_pro` |
| 7 | `kicad-cli pcb drc` | `drc.rpt` |

Fertigungsdaten danach mit:

```bash
python make_fabrication.py
```

## Stolpersteine, die hier gelöst sind

1. **`LM7812_TO220` hat keine eigenen Pins** — das Symbol erbt sie per `extends` von
   `LM7805_TO220`. Wird es unverändert eingebettet, zeichnet Eeschema ein leeres Kästchen.
   `build_schematic.py` klopft es flach und schreibt die Unit-Namen um.
2. **Der KiCad-Trafo-Footprint hat Geisterpads.** `Transformer_THT:Transformer_37x44` legt
   12 Kupferpads an, nummeriert aber nur 4. Die 8 netzlosen Pads wären blanke Kupferinseln
   neben 230 V~. `make_trafo_footprint.py` leitet einen sauberen 4-Pad-Footprint ab.
3. **`kicad-cli` überschreibt die `.kicad_pro`** und wirft dabei eigene Netzklassen weg.
   Deshalb läuft `setup_project.py` immer **als letzter Schritt**.
4. **`ZONE_FILLER` stürzt** auf einem frisch erzeugten Board ab (Segfault). Auf einem
   *geladenen* Board mit `BuildConnectivity()` läuft er durch — `build_pcb.py` macht
   deshalb den Umweg Speichern → Laden → Füllen → Speichern. Ohne das bliebe die
   Massefläche in den Gerber-Dateien leer.
5. **Bohrdateien werden nicht mitgeplottet.** `export gerbers` liefert keine `.drl`;
   `make_fabrication.py` ruft `export drill` separat auf und bricht ab, wenn die
   Bohrdatei fehlt — ein ZIP ohne `.drl` ist beim Fertiger unbrauchbar.

## Vor dem Bestellen bitte prüfen

1. **Trafo-Footprint gegen das Datenblatt abgleichen.** Der Footprint ist vom generischen
   KiCad-Trafo 37 × 44 mm abgeleitet: Primärpads bei x = 0 / 20,32 mm, Sekundärpads bei
   x = ±5,08 mm, Reihenabstand 25,4 mm. **Rastermaß und Pinbelegung des tatsächlich
   beschafften Trafos prüfen** und notfalls in `make_trafo_footprint.py` anpassen.
2. **Kühlkörper aussuchen** (≤ 15 K/W) und prüfen, ob er in die freigehaltenen
   19 × 14 mm passt.
3. **Elko-Bauhöhen** gegen das geplante Gehäuse prüfen (C1 ist Ø 16 mm).
4. Die **Sicherung sitzt nur in der Phase (L)**. Für allpolige Trennung gehört ein
   zweipoliger Schalter vor die Platine.

---
*RwTec · 2026 · erstellt mit Claude Code aus dem Referenz-Schaltbild.*
