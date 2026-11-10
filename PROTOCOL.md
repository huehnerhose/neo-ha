# S-Thermatik NEO – BLE protocol

Reverse engineered from PacketLogger captures of the S-Thermatik NEO app (iOS app running on a Mac). As of 2026-11-10, controller firmware 1-1.18.0, Bluetooth module 1.2.0.

## Device

| | |
|---|---|
| BLE name | `NEO basic` |
| Manufacturer (DIS) | ATech elektronika |
| BLE chip | Texas Instruments CC254x running TI's "SimpleBLEPeripheral" sample firmware (PnP vendor 0x000D, placeholder strings in the DIS) |
| Connections | only **one** at a time – the app and the ESP32/script lock each other out |
| Security | no pairing, no encryption |

## GATT

Service `FFF0`:

| Characteristic | Handle | Access | Usage |
|---|---|---|---|
| FFF1 | 0x25 | read/write | **Register addresses**: up to 5 × uint16 LE |
| FFF2 | 0x28 | read/write | **Register values**: 5 × int16 LE (read) or 1 × int16 LE (write) |
| FFF3 | – | write | not used by the app |
| FFF4 | – | notify | not used by the app (stays silent) |
| FFF5 | – | read | not used by the app |

The app only subscribes to the Service Changed indication (handle 0x0F ← `02 00`).

## Sequence

**Read**
1. FFF1 ← address list, e.g. `ce 1c 62 1e d4 1c f2 1e 98 1d` (= 0x1CCE 0x1E62 0x1CD4 0x1EF2 0x1D98)
2. wait (the app waits ~1.2 s; the BLE module apparently fetches the values from the stove controller via UART)
3. read FFF2 → 10 bytes = 5 × int16 LE, in the same order as the addresses

If you read too early, FFF2 still contains (parts of) the previous response. Robust approach: keep reading
until the content has changed **and** two consecutive reads are identical.

**Write**
1. FFF1 ← target address (2 bytes are enough; the app sometimes sends a list of 5, only the first address counts)
2. FFF2 ← value as int16 LE

## Registers

### Confirmed

| Address | Meaning | Values | R/W |
|---|---|---|---|
| 0x1D96 | Flue gas temperature | °C | R |
| 0x1E62 | Air damper | 0–100 % | R/W (writing only makes sense in manual mode) |
| 0x1CBE | Heating power | 1–3 | R/W |
| 0x1DEC | Air damper mode | 0 = automatic, 1 = manual | R/W |
| 0x1E7C | Door contact | 1 = open, 0 = closed | R |
| 0x1CCE | Constant | always 1234 – useful as a sanity check | R |

### Suspected / unclear

| Address | Observed | Guess |
|---|---|---|
| 0x1CD4 | 3 | Burn phase |
| 0x1EA2 | 23 | Room temperature |
| 0x1E82 | 3 → 2 → 1 | State/counter in the reloading sequence (drops when the door is opened) |
| 0x1D98 | 43–45 | ? |
| 0x1EF2 | −25 | ? |
| 0x1EF4 | 2519 | ? (operating hours/motor runtime?) |
| 0x1D4E | 7 | ? |
| 0x1E64 | 1 | ? |
| 0x1E2A, 0x1E8C, 0x1CDA–0x1CDE, 0x1F10 | 0 | ? |
| 0x1D76 | 2 | ? |
| 0x1E22 | 4 | ? (single query on connect) |

### On connect

```
FFF1 ← 1E46 1D98 1D96 1EF4 1EF6 ; FFF2 ← 0        (0x1E46 ← 0, purpose unknown – maybe session/login)
FFF1 ← 1ED6 1ED8 1E4A 1E4C 1F10 ; read FFF2 → 00 12 01 01 00 02 01 00 02 00   (version info, "1.18"?)
FFF1 ← 1E22 ; read FFF2
```

## App polling

The app queries these blocks in rotation:

```
A: 1CCE 1E62 1CD4 1EF2 1D98
B: 1E2A 1D4E 1E64 1CBE 1E82
C: 1EA2 1D96 1E8C 1DEC 1E7C
D: 1CDA 1CDC 1CDE 1EF2 1EA2
```

Additionally, on the "manual air damper" page:

```
1CDA 1CDC 1CDE 1F10 1D76
1DEC 1E62 1D98 1D96 1EF4
```

## Observed commands

| Action in the app | Commands |
|---|---|
| Heating power 1 / 2 / 3 | `0x1CBE ← 1/2/3` |
| Manual air damper 70 % | `0x1DEC ← 1`, `0x1E62 ← 70` |
| Manual air damper 40 % | `0x1DEC ← 1`, `0x1E62 ← 41` |
| Enable automatic mode | `0x1DEC ← 0` |
