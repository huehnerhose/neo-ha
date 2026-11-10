#!/usr/bin/env python3
"""PacketLogger trace (.pklg) -> ATT traffic as text.

Shows only ATT packets (L2CAP CID 0x0004), with time relative to the start of the trace.
NEO controller handles: 0x25 = FFF1 (addresses), 0x28 = FFF2 (values), 0x0F = CCCD Service Changed.

    python3 tools/pklg_dump.py captures/my-trace.pklg
"""
import struct
import sys

ATT = {
    0x01: "ErrRsp", 0x02: "MTUReq", 0x03: "MTURsp", 0x04: "FindInfoReq", 0x05: "FindInfoRsp",
    0x08: "ReadByTypeReq", 0x09: "ReadByTypeRsp", 0x0A: "ReadReq", 0x0B: "ReadRsp",
    0x10: "ReadByGrpReq", 0x11: "ReadByGrpRsp", 0x12: "WriteReq", 0x13: "WriteRsp",
    0x1B: "Notify", 0x1D: "Indicate", 0x52: "WriteCmd",
}
HANDLES = {0x25: "FFF1", 0x28: "FFF2", 0x0F: "CCCD"}


def records(data):
    i = 0
    while i + 13 <= len(data):
        length = struct.unpack("<I", data[i:i + 4])[0]
        secs, usecs = struct.unpack("<II", data[i + 4:i + 12])
        typ = data[i + 12]
        yield secs + usecs / 1e6, typ, data[i + 13:i + 4 + length]
        i += 4 + length


def regs(payload):
    return " ".join(f"{int.from_bytes(payload[j:j + 2], 'little'):04X}" for j in range(0, len(payload) - 1, 2))


def vals(payload):
    return " ".join(str(struct.unpack("<h", payload[j:j + 2])[0]) for j in range(0, len(payload) - 1, 2))


def main(path):
    t0 = None
    for t, typ, p in records(open(path, "rb").read()):
        if typ not in (2, 3) or len(p) < 9:
            continue
        cid = int.from_bytes(p[6:8], "little")
        if cid != 4:
            continue
        t0 = t if t0 is None else t0
        att = p[8:]
        op, body = att[0], att[1:]
        direction = "App->NEO" if typ == 2 else "NEO->App"
        name = ATT.get(op, f"0x{op:02X}")
        line = f"{t - t0:8.3f}  {direction}  {name:13}"
        if op in (0x12, 0x52, 0x0A) and len(body) >= 2:
            h = int.from_bytes(body[:2], "little")
            data = body[2:]
            line += f" {HANDLES.get(h, hex(h)):5} {data.hex(' ')}"
            if h == 0x25 and data:
                line += f"   [addresses: {regs(data)}]"
            elif h == 0x28 and data:
                line += f"   [value: {vals(data)}]"
        elif op == 0x0B:
            line += f"       {body.hex(' ')}   [{vals(body)}]"
        else:
            line += f"       {body.hex(' ')}"
        print(line)


if __name__ == "__main__":
    main(sys.argv[1])
