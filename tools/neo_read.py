#!/usr/bin/env python3
"""S-Thermatik NEO (BLE "NEO basic") - nur lesen.

Protokoll (aus PacketLogger-Trace abgeleitet):
  FFF1 <- bis zu 5 Registeradressen (uint16 LE)
  FFF2 -> 5 Werte (int16 LE)
Schreiben eines Registers (hier NICHT verwendet):
  FFF1 <- 1 Adresse, dann FFF2 <- Wert (int16 LE)

Vorher App auf iPhone/Mac schliessen - die Steuerung erlaubt nur eine Verbindung.
pip install bleak
"""
import asyncio, struct, time
from bleak import BleakClient, BleakScanner

FFF1 = "0000fff1-0000-1000-8000-00805f9b34fb"
FFF2 = "0000fff2-0000-1000-8000-00805f9b34fb"

# Registerblöcke wie die App sie abfragt
BLOCKS = [
    [0x1CCE, 0x1E62, 0x1CD4, 0x1EF2, 0x1D98],
    [0x1E2A, 0x1D4E, 0x1E64, 0x1CBE, 0x1E82],
    [0x1EA2, 0x1D96, 0x1E8C, 0x1DEC, 0x1E7C],
    [0x1CDA, 0x1CDC, 0x1CDE, 0x1EF2, 0x1EA2],
]
NAMES = {
    0x1E62: "Luftschieber",
    0x1D96: "Abgastemperatur",
    0x1CBE: "Heizleistung",
    0x1CD4: "Phase?",
    0x1EA2: "Raumtemp?",
}

DELAY = 0.6   # Sekunden zwischen Anfrage (FFF1) und Antwort (FFF2)

async def read_regs(client, regs):
    # Antwort der vorigen Anfrage merken, damit wir eine veraltete erkennen
    before = bytes(await client.read_gatt_char(FFF2))[:10]
    await client.write_gatt_char(FFF1, struct.pack("<5H", *regs), response=True)
    t0 = time.monotonic()
    await asyncio.sleep(DELAY)
    # warten, bis FFF2 sich geändert hat UND zweimal hintereinander gleich ist
    last = None
    data = before
    while time.monotonic() - t0 < 3.0:
        data = bytes(await client.read_gatt_char(FFF2))[:10]
        if data == last and data != before:
            break
        last = data
        await asyncio.sleep(0.3)
    vals = struct.unpack("<5h", data)
    if DEBUG:
        print("   ", " ".join(f"{r:04X}" for r in regs), "->", data.hex(" "), vals)
    return dict(zip(regs, vals))

DEBUG = True

async def main():
    dev = await BleakScanner.find_device_by_name("NEO basic", timeout=15)
    if not dev:
        print("NEO basic nicht gefunden (App noch verbunden?)")
        return
    async with BleakClient(dev) as client:
        print("verbunden:", dev)
        while True:
            vals = {}
            for b in BLOCKS:
                vals.update(await read_regs(client, b))
            line = "  ".join(f"{NAMES.get(r, hex(r))}={v}" for r, v in sorted(vals.items()))
            print(time.strftime("%H:%M:%S"), line, flush=True)
            await asyncio.sleep(5)

asyncio.run(main())
