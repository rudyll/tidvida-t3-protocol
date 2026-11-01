# TIDVIDA T3 protocol research (draft)

This is an independent, offline decoder for **already captured** DDAP response frames from the TIDVIDA T3 aquarium thermostat. It does not connect to a device or to Tuya, send requests, or control the thermostat. It is a candidate for a separate public repository; it has not been published.

## What is established

- The T3's Tuya model exposes ordinary data points 1 (current water temperature), 2 (target temperature), 7 (fault bitmap), 101 (device power), 102 (DDAP request), 103 (DDAP response), and 104 (temperature alarm). Data point 102 carries a raw request, not a power switch.
- The T3 Android panel resource version 1.1.19 identified the DDAP field names, wire types, scaling, and validity flags listed in `fields.json`. These are observations about this model and panel version, not a protocol guarantee for other devices.
- Historical response frames matched the 12-byte DDAP header and item structure. Extra measurements are commonly obtained by a DDAP GET request through Tuya's cloud. A response can be old even when the cloud API call itself just succeeded.
- Device power (DP101) was confirmed with a user-operated App on/off comparison. Cloud set temperature and power have separate field trials. The other App controls have not been mapped to safe, independently verified commands.

## Control inventory

| Function | Evidence | Status for this project |
| --- | --- | --- |
| Device power | DP101 model and user-operated App comparison; separate cloud field trial | Known cloud control; local control unavailable |
| Target water temperature | DP2 model and separate cloud field trial | Known cloud control; local control unavailable |
| Temperature alarm and fault | DP104 enum and DP7 bitmap model | Readable model fields; fault bit order and live behavior unverified |
| Pump, fan, temperature mode, display, sound, calibration | Controls visible in the T3 App | DDAP field IDs, ranges, effects, and recovery behavior not verified; no encoder provided |

The App's other controls must be traced to the T3 panel's own request construction and then checked against non-destructive, authorized observations before any control API is proposed.

## Offline use

```sh
python3 decode.py 44410181000c000100000000
python3 -m unittest discover -s tests
```

The first command is only a structural example with no items. Supply the hexadecimal bytes of a **response you already possess**. Do not publish raw captures without checking for identifiers or household telemetry.

The decoder reports all known fields in the frame and marks readings invalid if their item status is nonzero. Current water temperature and the two speed readings also require a true validity flag in the **same frame**; absent or false flags yield `null`, not zero or a previous reading. The tool does not decide whether a frame is fresh: callers must retain the original source timestamp and reject stale data themselves.

## Open work

| Route | Current evidence | Missing for cloud independence |
| --- | --- | --- |
| Tuya LAN 3.5 / TCP 6668 | Was readable earlier; recent connection and handshake attempts failed or were refused | A stable authenticated session and live DDAP read; no further blind retries |
| Tuya BLE | FD50 advertisements observed; one service discovery failed | Authenticated GATT exchange, T3 data mapping, and safe live read |
| Device cloud MQTT/TLS | Connection metadata observed | Device trust and protocol access; ordinary Surge HTTPS MITM does not decode MQTT |
| Tuya cloud API | Full telemetry and power available in field trials | Still depends on account, subscription and API access |

No local control, HA integration, multi-device compatibility, or ongoing reliability is claimed. Do not use an unverified control path for aquarium safety or maintenance automation.

## Sources

- [Tuya MQTT protocol](https://developer.tuya.com/en/docs/iot/MQTT-protocol?id=Kb65nphxrj8f1)
- [Tuya cloud device model](https://developer.tuya.com/en/docs/iot/equipment-related-interface?id=K9m1dlii6zkf7)
- [Tuya cloud properties](https://developer.tuya.com/en/docs/cloud/bd68171262?id=Kcp4utbhzzfgo)
- Field mapping was independently summarized from a locally downloaded T3 panel resource, version 1.1.19, and checked against previously captured frames. The manufacturer's source code and original captures are not included.

## Publication boundary

The draft includes no Tuya panel source, account credentials, device identifiers, private packets, or household measurements. Before public release, review the chosen license, provenance of every file, product naming, and at least one independently obtained synthetic or redacted fixture. Manufacturer protocol facts should remain attributed to the observations; this project is unaffiliated with TIDVIDA or Tuya.
