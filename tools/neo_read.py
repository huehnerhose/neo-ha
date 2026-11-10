#!/usr/bin/env python3
"""S-Thermatik NEO (BLE "NEO basic") - read only.

Protocol (derived from PacketLogger traces):
  FFF1 <- up to 5 register addresses (uint16 LE)
  FFF2 -> 5 values (int16 LE)
Writing a register (NOT used here):
  FFF1 <- 1 address, then FFF2 <- value (int16 LE)

Close the app on iPhone/Mac first - the controller only allows one connection.
pip install bleak
"""
import asyncio, struct, time
from bleak import BleakClient, BleakScanner

FFF1 = "0000fff1-0000-1000-8000-00805f9b34fb"
FFF2 = "0000fff2-0000-1000-8000-00805f9b34fb"

# Register blocks as queried by the app
BLOCKS = [
    [0x1CCE, 0x1E62, 0x1CD4, 0x1EF2, 0x1D98],
    [0x1E2A, 0x1D4E, 0x1E64, 0x1CBE, 0x1E82],
    [0x1EA2, 0x1D96, 0x1E8C, 0x1DEC, 0x1E7C],
    [0x1CDA, 0x1CDC, 0x1CDE, 0x1EF2, 0x1EA2],
]
NAMES = {
    0x1E62: "air_damper",
    0x1D96: "flue_gas_temp",
    0x1CBE: "heating_power",
    0x1CD4: "phase?",
    0x1EA2: "room_temp?",
}

DELAY = 0.6   # seconds between request (FFF1) and response (FFF2)

async def read_regs(client, regs):
    # remember the previous response so we can detect a stale one
    before = bytes(await client.read_gatt_char(FFF2))[:10]
    await client.write_gatt_char(FFF1, struct.pack("<5H", *regs), response=True)
    t0 = time.monotonic()
    await asyncio.sleep(DELAY)
    # wait until FFF2 has changed AND is identical twice in a row
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
        print("NEO basic not found (is the app still connected?)")
        return
    async with BleakClient(dev) as client:
        print("connected:", dev)
        while True:
            vals = {}
            for b in BLOCKS:
                vals.update(await read_regs(client, b))
            line = "  ".join(f"{NAMES.get(r, hex(r))}={v}" for r, v in sorted(vals.items()))
            print(time.strftime("%H:%M:%S"), line, flush=True)
            await asyncio.sleep(5)

asyncio.run(main())
