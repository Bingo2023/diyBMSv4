# ModuleV450 – Bolt-on 123 mm, Rev B (EMV-optimiert)

Zellmodul DIYBMS v4.5 (ATtiny1624) im Format der BMS_alt (DIYBMS Lishen/EVE v1.7),
direkt auf die Zellpole geschraubt. Rev B ersetzt Rev A.

## Mechanik
| | |
|---|---|
| Platine | 154,5 × 31,5 mm (ohne Lasche) |
| Lochabstand | **123,0 mm** |
| Löcher | **6,3 mm** gebohrt, durchkontaktiert (JLC-Maximum), Ø 15 mm blanker Kupferring oben + unten, 16 Stitching-Löcher Ø 0,6 mm |
| Links / rechts | Zell-Plus (BAT+) / Zell-Minus (GND) |
| Lagen | 2, 1,6 mm FR4, 1 oz |

## Layout-Konzept Rev B (EMV)
* **Zwei Zonen:** ruhige Zone (Plus-Seite, x ≈ 12–48 mm) mit µC, Referenz D1, Optokoppler,
  Temperatursensoren, Steckern. Lastzone (x ≈ 51–116 mm) mit allen 16 Lastwiderständen,
  MOSFET Q1 und Minus-Bolzen.
* **Leistungspfade als Kupferflächen statt Leiterbahnen:**
  VCC-Einspeisung 5,8 mm breit an der Oberkante, VCC-Sammelschiene 5,4 mm,
  Reihenknoten zwischen den Widerständen je 6 × 4,2 mm, **DRAIN-Schiene 8,3 mm** über die volle Höhe
  bis an alle 4 Drain-Pins von Q1, **Source-Fläche 14 × 11 mm** von den 3 Source-Pins direkt zum Minus-Bolzen.
  Restliche Power-Bahnen 1,5 mm.
* **Laststrom-Rückweg:** Q1-Source → Kupferfläche oben → Minus-Bolzen.
  Der getaktete Laststrom fließt nicht über die Massefläche des µC.
* **Sternpunkt-Versorgung:** Der µC wird über einen eigenen Zweig versorgt
  (F1 → TVS D2 → C2 10 µF → C1 100 nF → U2 Pin 1). Er hängt nicht an der Lastschiene,
  daher misst der ADC keinen Spannungsabfall durch den Balancing-Strom.
* **Unterseite:** durchgehende GND-Fläche als Bezug und Schirm, nur am Minus-Bolzen
  mit dem Lastpfad verbunden (Sternpunkt).
* Abstand µC ↔ Lastblock ≈ 20 mm, µC ↔ Q1 ≈ 65 mm.
* Der Board-Temperatursensor R32 sitzt bewusst am Rand der ruhigen Zone, direkt neben dem Lastblock.

## Elektrik
* Last: **16 × 1,2 Ω 2512 (1 W, UniOhm 25121WF120KT4E, LCSC C46193)** – gleiche Widerstände wie BMS_alt.
  4 Stränge à 4 in Reihe, parallel = **1,2 Ω** (BMS_alt ebenfalls 1,2 Ω gesamt) → **gleicher Strom wie die alte Platine**:
  3,2 V: 2,6 A / 8,5 W · 3,4 V: 2,8 A / 9,6 W · **3,65 V: 3,0 A / 11,1 W** (0,69 W je Widerstand).
  In der Firmware den Lastwiderstand auf 1,2 Ω setzen.
* **Q1 = AO4402** (SO-8, 20 V, 20 A, R_DS(on) max 7 mΩ bei U_GS = 2,5 V, LCSC C115828)
  statt AO3400A (SOT-23) bzw. LONTEN LNG045R210 (TO-252, BMS_alt). Bei 3 A ≈ 63 mW Verlust. Voll durchgesteuert auch bei LiFePO4-Zellspannung (U_GS ≈ 3 V).
  Gate über R35 510 Ω, Pulldown R36 10 kΩ (wie V450).
* **F1 = Littelfuse 2920L500/24SLDR** (PTC 2920, 5 A Halten / 10 A Auslösen, 24 V, 3 mΩ, LCSC C1512058)
  statt mSMD150. Hält bei 60–70 °C noch ≈ 3,5 A, also über dem Balancing-Strom von max. 3,0 A
  (die BMS_alt hatte nur 3 A Halten = genau an der Grenze). Spannungsabfall bei 3 A ≈ 9 mV, Verlust ≈ 27 mW.
* **Comms: TX1/RX1 = Molex PicoBlade 53261-0271** (1,25 mm, 2-polig, SMD liegend, LCSC C177225), passend zu den
  „Mini Micro JST 1,25 mm“-Kabeln. Kabelausgang an der Unterkante, von JLC mitbestückt.
  Pin 1 TX: TXOUT1 / Pin 2: TXOUT2 · RX: Pin 1 RXD0 / Pin 2 VCC (wie V450).
* Zelltemperatur: NTC R23 an der Unterkante direkt neben dem Plus-Bolzen; auf der Unterseite liegt darunter eine
  Kupferfläche am Plus-Pol als Wärmebrücke. Lasche, J1 und J3 entfallen.
  **R23B** = Bestückoption (nicht bestückt, gleiche Netze PA3/ENABLE) direkt am Lastblock links neben der
  VCC-Schiene. Nur R23 **oder** R23B bestücken.
* Umbenennung gegenüber V450: R14→R35, R15→R36, R16→R30, R17→R37, R18→R34, R19→R32, R20→R33, R21→R31;
  Lastwiderstände R6–R21.

## Prüfung
KiCad-DRC: 0 Fehler, 0 offene Verbindungen (nur Silkscreen-Hinweise).

## Dateien
* `ModuleV450_Bolt123_revB_gerber_jlc.zip` – Gerber + Bohrdaten für JLCPCB
* `ModuleV450_Bolt123_revB_bom_jlc.csv` / `_cpl_jlc.csv` – SMT-Bestückung Oberseite
* `ModuleV450_Bolt123_revB_bom_full.csv` – vollständige Stückliste
* `ModuleV450_Bolt123_revB.kicad_pcb` – KiCad-7-Layout, `scripts/` – Generator-Skripte

Handbestückung: nur optional UPDI1 und ggf. R23B (statt R23).

## JLCPCB
FR-4, 2 Lagen, 1,6 mm, grün, LeadFree HASL, 16 Stück, PCB Assembly Top Side mit BOM + CPL.
Drehungen in der JLC-Vorschau prüfen (SOIC-8/-14, SOP-4, SOT-23 und SMB sind wie bei V450 korrigiert).

## Firmware-Update über die RX/TX-Kette

Für diese Platine gibt es ein Firmware-Update über die vorhandene RX/TX-Kette vom ESP32 aus,
ohne Änderung der Hardware: Fork `Bingo2023/diyBMSv4ESP32`, Branch `fw-update-ueber-kette`,
Firmware-Umgebungen `V450_BL_5K` / `V450_BL_10K` (Lastwiderstand dort bereits 1,2 Ω).
Einmalig je Modul Bootloader und Firmware per UPDI (Steckplatz UPDI1, Stiftleiste nur einstecken),
danach alle Updates über den Controller. Anleitung: `README_FIRMWAREUPDATE_KETTE.md` im Firmware-Repo.
