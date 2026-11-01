"""Decode a previously captured TIDVIDA T3 DDAP DATA frame; no network I/O."""

import json
import sys
from pathlib import Path


FIELDS = json.loads(Path(__file__).with_name("fields.json").read_text())
MAX_FRAME = 512


def decode(frame: bytes) -> dict:
    if len(frame) < 12 or len(frame) > MAX_FRAME:
        raise ValueError("frame length outside 12..512 bytes")
    if frame[:3] != b"DA\x01" or frame[3] != 0x81:
        raise ValueError("expected DDAP v1 DATA response")
    if frame[5] != 12:
        raise ValueError("unsupported header length")
    count = int.from_bytes(frame[8:10], "big")
    body_length = int.from_bytes(frame[10:12], "big")
    if len(frame) != 12 + body_length:
        raise ValueError("body length mismatch")

    offset = 12
    items = {}
    for _ in range(count):
        if offset + 6 > len(frame):
            raise ValueError("truncated item header")
        field_id = frame[offset:offset + 2].hex()
        wire_type = frame[offset + 2]
        status = frame[offset + 3]
        value_length = int.from_bytes(frame[offset + 4:offset + 6], "big")
        offset += 6
        if offset + value_length > len(frame):
            raise ValueError("truncated item value")
        value = frame[offset:offset + value_length]
        offset += value_length
        if field_id in items:
            raise ValueError("duplicate field")
        spec = FIELDS.get(field_id)
        if spec is None:
            continue
        if wire_type != spec["type"] or value_length != (1 if wire_type == 1 else 4):
            raise ValueError(f"wrong type or length for {field_id}")
        if wire_type == 1 and value not in (b"\x00", b"\x01"):
            raise ValueError(f"invalid boolean for {field_id}")
        raw = bool(value[0]) if wire_type == 1 else int.from_bytes(value, "big", signed=wire_type == 2)
        items[field_id] = {"name": spec["name"], "value": raw / 10 ** spec.get("scale", 0) if wire_type != 1 else raw,
                           "unit": spec.get("unit"), "status": status}
    if offset != len(frame):
        raise ValueError("trailing bytes or item count mismatch")

    for field_id, item in items.items():
        spec = FIELDS[field_id]
        flag_id = spec.get("validity")
        flag = items.get(flag_id) if flag_id else None
        if item["status"] != 0 or (flag_id and (not flag or flag["status"] != 0 or flag["value"] is not True)):
            item["value"] = None
    return {"request_id": int.from_bytes(frame[6:8], "big"), "items": items}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 decode.py HEX_DATA_FRAME")
    try:
        print(json.dumps(decode(bytes.fromhex(sys.argv[1])), indent=2, ensure_ascii=False))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
