# neo-ha

S-Thermatik NEO Kaminsteuerung („NEO basic“, Bluetooth LE) in Home Assistant einbinden.

Das Protokoll ist in [PROTOCOL.md](PROTOCOL.md) dokumentiert: ein einfaches Register-Protokoll über
die Characteristics FFF1 (Adressen) und FFF2 (Werte), ohne Pairing oder Verschlüsselung.

## Inhalt

| Pfad | |
|---|---|
| `esphome/kamin-neo.yaml` | ESPHome-Konfiguration für einen ESP32 am Kamin → Home Assistant |
| `tools/neo_read.py` | Python-Skript (bleak), liest die Register zyklisch aus – nur lesend |
| `tools/pklg_dump.py` | wandelt PacketLogger-Traces in lesbaren ATT-Verkehr um |
| `captures/` | eigene PacketLogger-Mitschnitte (nicht im Repo, siehe `.gitignore`) |

## ESPHome

1. `esphome/secrets.yaml` aus `secrets.yaml.example` anlegen.
2. `kamin-neo.yaml` auf einen ESP32 flashen (kein ESP8266 – der hat kein Bluetooth).
3. Handy-App schließen, im ESPHome-Log nach `NEO basic gefunden: XX:XX:…` suchen.
4. Die MAC unter `ble_client → mac_address` eintragen, neu flashen.
5. In Home Assistant über die ESPHome-Integration hinzufügen.

Entitäten: Abgastemperatur, Luftschieber, Heizleistung, Kamintür, Luftschieber manuell (Status),
Raumtemperatur (?), Phase (Rohwert), sowie zum Steuern *Heizleistung einstellen*,
*Luftschieber manuell setzen* und *Luftschieber Automatik*.

Die Steuerung erlaubt nur **eine** Bluetooth-Verbindung. Mit dem Schalter
„Kamin Bluetooth verbunden“ trennt der ESP32 die Verbindung, damit die Handy-App wieder zugreifen kann.

> **Ungetestet auf dem ESP32.** Erst das Lesen prüfen, dann die Steuerung einmal mit der App gegenchecken.
> Nach manuellem Luftschieber die Automatik wieder einschalten.

## Python-Skript

```sh
pip install bleak
python3 tools/neo_read.py | tee abbrand.log
```

Die Handy-App muss dabei geschlossen sein.

## Traces lesen

```sh
python3 tools/pklg_dump.py captures/mein-trace.pklg
```

Mitschneiden: PacketLogger aus den „Additional Tools for Xcode“ (developer.apple.com/download/all),
iOS-App auf dem Mac starten, nachdem die Aufzeichnung läuft.

> Traces enthalten neben dem Kamin auch Bluetooth-Werbung anderer Geräte in Reichweite
> (Gerätenamen wie iPhone, AirPods). Deshalb ist `captures/` in der `.gitignore`.
