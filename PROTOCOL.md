# S-Thermatik NEO – BLE-Protokoll

Reverse Engineering aus PacketLogger-Mitschnitten der S-Thermatik-NEO-App (iOS-App auf dem Mac). Stand: 10.11.2026, Steuerung 1-1.18.0, Bluetooth-Modul 1.2.0.

## Gerät

| | |
|---|---|
| BLE-Name | `NEO basic` |
| Hersteller (DIS) | ATech elektronika |
| BLE-Chip | Texas Instruments CC254x mit TI-Beispielfirmware „SimpleBLEPeripheral“ (PnP Vendor 0x000D, Platzhalter-Strings im DIS) |
| Verbindungen | nur **eine** gleichzeitig – App und ESP32/Skript schließen sich gegenseitig aus |
| Sicherheit | kein Pairing, keine Verschlüsselung |

## GATT

Service `FFF0`:

| Characteristic | Handle | Rechte | Verwendung |
|---|---|---|---|
| FFF1 | 0x25 | read/write | **Registeradressen**: bis zu 5 × uint16 LE |
| FFF2 | 0x28 | read/write | **Registerwerte**: 5 × int16 LE (lesen) bzw. 1 × int16 LE (schreiben) |
| FFF3 | – | write | von der App nicht benutzt |
| FFF4 | – | notify | von der App nicht benutzt (bleibt still) |
| FFF5 | – | read | von der App nicht benutzt |

Die App abonniert nur die Service-Changed-Indication (Handle 0x0F ← `02 00`).

## Ablauf

**Lesen**
1. FFF1 ← Adressliste, z. B. `ce 1c 62 1e d4 1c f2 1e 98 1d` (= 0x1CCE 0x1E62 0x1CD4 0x1EF2 0x1D98)
2. warten (die App wartet ~1,2 s; das BLE-Modul holt die Werte offenbar per UART von der Ofensteuerung)
3. FFF2 lesen → 10 Byte = 5 × int16 LE, in derselben Reihenfolge wie die Adressen

Wird zu früh gelesen, enthält FFF2 noch (Teile) der vorigen Antwort. Robust: lesen, bis sich der
Inhalt geändert hat **und** zwei Lesungen hintereinander gleich sind.

**Schreiben**
1. FFF1 ← Zieladresse (2 Byte genügen; die App schickt teils eine 5er-Liste, maßgeblich ist die erste Adresse)
2. FFF2 ← Wert als int16 LE

## Register

### Gesichert

| Adresse | Bedeutung | Werte | R/W |
|---|---|---|---|
| 0x1D96 | Abgastemperatur | °C | R |
| 0x1E62 | Luftschieber | 0–100 % | R/W (W nur im Manuellbetrieb sinnvoll) |
| 0x1CBE | Heizleistung | 1–3 | R/W |
| 0x1DEC | Luftschieber-Modus | 0 = Automatik, 1 = manuell | R/W |
| 0x1E7C | Türkontakt | 1 = offen, 0 = zu | R |
| 0x1CCE | Konstante | immer 1234 – gut als Plausibilitätsprüfung | R |

### Vermutet / unklar

| Adresse | beobachtet | Vermutung |
|---|---|---|
| 0x1CD4 | 3 | Abbrandphase |
| 0x1EA2 | 23 | Raumtemperatur |
| 0x1E82 | 3 → 2 → 1 | Zustand/Zähler im Nachlege-Ablauf (fällt beim Türöffnen) |
| 0x1D98 | 43–45 | ? |
| 0x1EF2 | −25 | ? |
| 0x1EF4 | 2519 | ? (Betriebsstunden/Motorlaufzeit?) |
| 0x1D4E | 7 | ? |
| 0x1E64 | 1 | ? |
| 0x1E2A, 0x1E8C, 0x1CDA–0x1CDE, 0x1F10 | 0 | ? |
| 0x1D76 | 2 | ? |
| 0x1E22 | 4 | ? (Einzelabfrage beim Verbinden) |

### Beim Verbinden

```
FFF1 ← 1E46 1D98 1D96 1EF4 1EF6 ; FFF2 ← 0        (0x1E46 ← 0, Zweck unbekannt – evtl. Session/Anmeldung)
FFF1 ← 1ED6 1ED8 1E4A 1E4C 1F10 ; FFF2 lesen → 00 12 01 01 00 02 01 00 02 00   (Versionsinfo, „1.18“?)
FFF1 ← 1E22 ; FFF2 lesen
```

## Polling der App

Die App fragt reihum diese Blöcke ab:

```
A: 1CCE 1E62 1CD4 1EF2 1D98
B: 1E2A 1D4E 1E64 1CBE 1E82
C: 1EA2 1D96 1E8C 1DEC 1E7C
D: 1CDA 1CDC 1CDE 1EF2 1EA2
```

Auf der Seite „Luftschieber manuell“ zusätzlich:

```
1CDA 1CDC 1CDE 1F10 1D76
1DEC 1E62 1D98 1D96 1EF4
```

## Beobachtete Befehle

| Aktion in der App | Befehle |
|---|---|
| Heizleistung 1 / 2 / 3 | `0x1CBE ← 1/2/3` |
| Luftschieber manuell 70 % | `0x1DEC ← 1`, `0x1E62 ← 70` |
| Luftschieber manuell 40 % | `0x1DEC ← 1`, `0x1E62 ← 41` |
| Automatik aktivieren | `0x1DEC ← 0` |
