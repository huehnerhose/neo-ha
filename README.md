# neo-ha

Integrate the S-Thermatik NEO fireplace controller ("NEO basic", Bluetooth LE) into Home Assistant.

The protocol is documented in [PROTOCOL.md](PROTOCOL.md): a simple register protocol over
the characteristics FFF1 (addresses) and FFF2 (values), with no pairing or encryption.

## Contents

| Path | |
|---|---|
| `esphome/kamin-neo.yaml` | ESPHome configuration for an ESP32 next to the fireplace → Home Assistant |
| `esphome/lang/en.yaml`, `esphome/lang/de.yaml` | entity names in English / German |
| `tools/neo_read.py` | Python script (bleak) that reads the registers periodically – read only |
| `tools/pklg_dump.py` | converts PacketLogger traces into readable ATT traffic |
| `captures/` | your own PacketLogger captures (not in the repo, see `.gitignore`) |

## ESPHome

1. Create `esphome/secrets.yaml` from `secrets.yaml.example`.
2. Pick the entity language in `kamin-neo.yaml` (see below).
3. Flash `kamin-neo.yaml` to an ESP32 (not an ESP8266 – it has no Bluetooth).
4. Close the phone app and look for `Found NEO basic: XX:XX:…` in the ESPHome log.
5. Enter the MAC under `ble_client → mac_address` and flash again.
6. Add the device in Home Assistant via the ESPHome integration.

### Entity language

Entity names come from a language file that is included as a package. English is the default;
for German, swap the comment in `kamin-neo.yaml`:

```yaml
packages:
  # lang: !include lang/en.yaml
  lang: !include lang/de.yaml
```

Pick the language before adding the device to Home Assistant. Switching later renames the entities,
and newly added entities get entity IDs based on the new names.

| English | German | Type |
|---|---|---|
| Flue gas temperature | Abgastemperatur | sensor (°C) |
| Air damper | Luftschieber | sensor (%) |
| Heating power | Heizleistung | sensor (1–3) |
| Room temperature (?) | Raumtemperatur (?) | sensor (°C), unconfirmed |
| Phase (raw value) | Phase (Rohwert) | sensor, unconfirmed |
| Register 1E82 / 1D98 | Register 1E82 / 1D98 | sensor, raw value |
| Air damper manual | Luftschieber manuell | binary sensor |
| Fireplace door | Kamintür | binary sensor (door) |
| Set heating power | Heizleistung einstellen | number (1–3) |
| Set air damper manually | Luftschieber manuell setzen | number (0–100 %) |
| Air damper automatic | Luftschieber Automatik | switch |
| Fireplace Bluetooth connected | Kamin Bluetooth verbunden | switch |

To add another language, copy `lang/en.yaml`, translate the values and include the new file.

The controller only allows **one** Bluetooth connection. Turning off the
"Fireplace Bluetooth connected" switch makes the ESP32 disconnect so the phone app can connect again.

> **Untested on the ESP32.** Verify reading first, then cross-check the controls once against the app.
> After using the manual air damper, switch automatic mode back on.

## Python script

```sh
pip install bleak
python3 tools/neo_read.py | tee burn.log
```

The phone app must be closed while it runs.

## Reading traces

```sh
python3 tools/pklg_dump.py captures/my-trace.pklg
```

Capturing: use PacketLogger from the "Additional Tools for Xcode" (developer.apple.com/download/all)
and start the iOS app on the Mac after recording has started.

> Besides the fireplace, traces also contain Bluetooth advertisements from other devices in range
> (device names such as iPhone, AirPods). That is why `captures/` is in `.gitignore`.
