# Platinenentwurf mit KiCad und Claude Code — ein Werkstattbericht

> **Kurzfassung:** Aus einem Schaltbild als Bilddatei ist in rund **55 Minuten** eine
> fertige, geprüfte Leiterplatte geworden: ein Netzteil 230 V~ → +12 V mit dem
> Festspannungsregler 7812. Vorgegeben waren ein Screenshot und ein erklärender Text —
> herausgekommen sind Schaltplan, geroutete Platine (92 × 77 mm, ==ERC 0, DRC 0==) und
> ein vollständiger Satz Produktionsdateien. Besonderheit: Der Entwurf entstand nicht
> durch Klicken in KiCad, sondern über **Generatorskripte**, und KiCad selbst diente als
> Prüfinstanz.

---

## 🧭 Die Vorgabe

Ausgangspunkt war ein Bild mit Schaltung und Beschreibung — das klassische
Lehrbuch-Netzteil:

![Vorgabe: Schaltbild des einfachen Netzteils](Platine7812.png)

Der Text dazu beschreibt den Signalweg: Der Trafo **TR1** setzt die Netzspannung von
230 V auf eine kleinere Wechselspannung herunter, vier Dioden **1N4007** richten sie
gleich, **C1/C2** sieben sie, der **LM78XX** stabilisiert auf die gewünschte
Gleichspannung, **C3/C4** bügeln Restbrummen glatt. Heraus kommen an **JP1/JP2** die
+12 V gegen Masse.

Meine Vorgabe an Claude Code war knapp: *„möchte mit KiCad eine Platine gebaut haben mit
Festspannungsregler 7812 sowie in der Bilddatei beschrieben"* — plus der Hinweis, dass
ich in KiCad bereits ein leeres Projekt **Platine7812** angelegt hatte.

---

## 📐 Zwei Rückfragen vorab

Bevor irgendetwas gebaut wurde, kamen zwei Fragen, die das Bild nicht beantwortet:

| Frage | Meine Entscheidung |
|---|---|
| Trafo **auf** der Platine oder extern? | auf der Platine — wie im Bild |
| Welcher Ausgangsstrom? | ca. **0,5 A** |

Das war gut investiert: An diesen zwei Antworten hängen Platinengröße, Bauteilwerte,
Kühlkörper und die Sicherheitsabstände zur Netzspannung.

---

## 🛠️ Die Umsetzung

Der eigentliche Kniff: Statt Bauteile in KiCad zusammenzuklicken, schrieb Claude Code
**Python-Skripte, die das Projekt erzeugen**. Der Ablauf in groben Zügen:

1. **🔬 Bibliotheken inspizieren.** Erst nachsehen, wie die Bauteile in KiCad wirklich
   heißen und wo ihre Anschlüsse liegen — nicht raten.
2. **📐 Schaltplan erzeugen.** Jedes Bauteil bekommt ein kurzes Leitungsstück mit einem
   Netz-Namen. Gleiche Namen sind elektrisch verbunden — das ist robuster, als Drähte zu
   zeichnen.
3. **✅ ERC laufen lassen.** KiCads Schaltplanprüfung meldete erst 10 Verstöße, nach
   Korrektur **0**.
4. **📦 Netzliste exportieren.** Sie ist ab hier die ==einzige Quelle der Wahrheit== —
   die Platine wird direkt aus ihr aufgebaut, nicht von Hand nachgepflegt.
5. **🔧 Platine bauen.** Bauteile setzen, Leiterbahnen ziehen, Massefläche füllen.
6. **✅ DRC laufen lassen** — und zwar mehrfach, siehe unten.

Am Ende steht ein einziger Befehl, der alles reproduziert:

```
python build_all.py
```

Wenn ich morgen den Elko C1 auf 3300 µF ändern will, ändere ich eine Zeile und lasse das
Skript laufen. Schaltplan, Netzliste, Platine und Prüfberichte sind danach wieder
konsistent — ein Abgleich von Hand entfällt.

---

## 🔬 Was die Prüfungen gefunden haben

Das ist der Teil, der mich am meisten überzeugt hat. KiCads eigene Prüfwerkzeuge haben
Fehler gefunden, die man im Layout leicht übersieht:

- ⚠️ **Zwei echte Kurzschlüsse.** Eine Leiterbahn lief mitten durch ein fremdes Lötauge
  — einmal die Phase durch den Neutralleiter-Anschluss, einmal Masse durch den
  Reglereingang. Auf dem Bildschirm sieht so etwas aus wie eine normale gerade Linie.
- ⚠️ **Geisterpads am Trafo.** Der mitgelieferte KiCad-Trafo-Footprint legt 12 Kupferpads
  an, benennt aber nur 4. Die übrigen 8 hätten als blanke Kupferinseln ==direkt neben
  230 V~== auf der fertigen Platine gesessen. Claude Code hat daraus einen eigenen,
  sauberen Footprint mit genau 4 Anschlüssen abgeleitet.
- ⚠️ **Zu enge Abstände bei Netzspannung.** Dafür wurde eine eigene Entwurfsregel
  hinterlegt: *mindestens 6,4 mm zwischen Primär- und Sekundärkreis*. KiCad rechnet das
  jetzt bei jedem Durchlauf nach, statt dass man sich auf eine gezeichnete Trennlinie
  verlässt. Auch die Netzklemme wurde deshalb von 5,08 mm auf **10 mm Raster** getauscht.

> Ein Layout, das „richtig aussieht", ist nicht geprüft. Erst ERC und DRC machen daraus
> eine belastbare Aussage.

---

## 💡 Zwei Werte, die vom Bild abweichen

Beim Nachrechnen fielen zwei Punkte auf, die bewusst anders umgesetzt wurden:

**🔑 Sekundärspannung 15 V~ statt der im Text genannten 18 V~.** Die Rechnung:

```
15 V~ → Scheitelwert 15 · √2                     = 21,2 V
        − 2 Diodenflussspannungen (2 · 0,7 V)    = 19,8 V
        − Brummspannung  I·t/C = 0,5 A · 10 ms / 2200 µF = 2,3 V
        → am Reglereingang bleiben               ≈ 17,5 V
```

Der 7812 braucht mindestens 14 V — es bleiben **3,5 V Reserve**. Die überschüssige
Spannung verheizt der Regler: Mit 15 V~ sind das **3,3 W**, mit 18 V~ wären es **5,5 W**
gewesen.

**🔑 Trafo 15 VA statt 10 VA.** Bei Gleichrichtung mit Ladeelko fließt der Strom nicht
gleichmäßig, sondern in kurzen Spitzen. Der Effektivstrom im Trafo ist deshalb rund
**1,6- bis 1,8-mal so hoch** wie der Gleichstrom am Ausgang — für 0,5 A also etwa 0,85 A.
Ein 10-VA-Trafo liefert bei 15 V nur 0,67 A und wäre überlastet gewesen. Die Sicherung
wurde entsprechend auf T 160 mA angepasst.

---

## 📦 Das Endprodukt

![Fertige Platine in der 3D-Ansicht von KiCad](Platine7812in3d.png)

Oben die **Primärseite** mit Netzklemme, Feinsicherung (hochkant, spart 16 mm Breite) und
Trafo. Darunter die durchgezogene **Isolationsbarriere**. Unten die **Sekundärseite** mit
Brückengleichrichter, Ladeelko, Regler samt freigehaltener Kühlkörperfläche und den
beiden Ausgangsstiften.

| Kennwert | Wert |
|---|---|
| Größe | 92,2 × 77,2 mm, 2 Lagen, bedrahtet (THT) |
| ERC / DRC | **0 / 0 Verstöße**, 0 unverbundene Anschlüsse |
| Kriechstrecke Primär ↔ Sekundär | ≥ 6,4 mm, per Regel nachgerechnet |
| Leiterbahnen | 50 Segmente, nur 2 Durchkontaktierungen |

Dass die Platine **unter 100 × 100 mm** bleibt, war Absicht: Unterhalb dieser Grenze
fertigen die üblichen Anbieter deutlich günstiger. Dafür wanderte die gesamte
Sekundärseite unter den Trafo.

**🎯 Kreuzungsfreie Brücke.** Ein hübsches Detail: Durch Drehen von zwei der vier Dioden
um 180° liegen die Anschlüsse so, dass der Gleichrichter ganz ohne Leitungskreuzung
auskommt:

```
AC1 --|<|-- VRAW   VRAW --|<|-- AC2     obere Reihe
AC1 --|<|-- GND    GND  --|<|-- AC2     untere Reihe
```

### Produktionsdateien

Im Ordner `Platine7812/fertigung` liegt alles Nötige:

| Datei | Zweck |
|---|---|
| `Platine7812_Fertigung.zip` | **das, was der Fertiger bekommt** — 7 Gerber-Lagen + Bohrdatei |
| `Platine7812.drl` | Bohrdatei (Excellon) |
| `Platine7812_BOM.csv` | Stückliste |
| `Platine7812_Schaltplan.pdf` | Schaltplan |
| `Platine7812_Bestueckung.pdf` | Bestückungsplan |

⚠️ Eine Falle, die hier bewusst abgesichert ist: KiCads „Plot"-Funktion erzeugt **nur die
Gerber-Dateien, nicht die Bohrdatei**. Ein ZIP ohne `.drl` ist beim Fertiger unbrauchbar.
Das Skript ruft den Bohrdatei-Export deshalb separat auf und bricht ab, wenn die Datei
fehlt.

---

## ⚠️ Was vor der Bestellung noch zu tun ist

1. **Trafo-Anschlussmaße prüfen.** Der Footprint ist vom generischen KiCad-Trafo
   37 × 44 mm abgeleitet. Sobald der reale 15-VA-Trafo da ist, gehört sein Datenblatt
   gegen die Pad-Abstände gehalten. Nach oben sind nur 2,4 mm Luft zur Platinenkante.
2. **Kühlkörper aussuchen** (≤ 15 K/W). Die Fläche von 19 × 14 mm ist freigehalten. Ohne
   Kühlkörper schaltet der 7812 bei 3,3 W thermisch ab.

---

## ✅ Fazit

Rund **55 Minuten** von der Bilddatei zur prüfbaren Platine — das Bemerkenswerte daran
ist weniger das Tempo als die **Nachvollziehbarkeit**. Jeder Schritt steckt in einem
Skript, jede Designentscheidung ist im Code kommentiert, und die Aussage „das passt"
kommt nicht aus dem Bauchgefühl, sondern aus KiCads eigenen Prüfwerkzeugen.

Für den Unterricht ist genau das der interessante Teil: Man kann zeigen, *warum* die
Netzklemme 10 mm Raster hat, *warum* 15 V~ besser sind als 18 V~ und *was* ein
Kurzschluss-Fund im DRC-Bericht bedeutet — und alles mit einem Befehl noch einmal
nachvollziehen.

> ⚠️ **Sicherheitshinweis:** Die Primärseite führt 230 V~. Aufbau und Messung nur durch
> qualifizierte Personen, mit Trenntrafo und niemals bei offenem Gehäuse.

![](logorw96.png)

*Erstellt: 2026-09-25 · KiCad 8.0.8 · kiutils / pcbnew / kicad-cli · Claude Code + Rw*
