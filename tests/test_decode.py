import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location("ddap_decode", Path(__file__).resolve().parents[1] / "decode.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def frame(*items):
    body = b"".join(bytes.fromhex(field_id) + bytes((wire_type, status)) + len(value).to_bytes(2, "big") + value
                    for field_id, wire_type, status, value in items)
    return b"DA\x01\x81\x00\x0c\x12\x34" + len(items).to_bytes(2, "big") + len(body).to_bytes(2, "big") + body


class DecodeTests(unittest.TestCase):
    def test_signed_temperature_and_valid_zero_speed(self):
        result = module.decode(frame(("5003", 2, 0, (-25).to_bytes(4, "big", signed=True)),
                                     ("200b", 3, 0, (0).to_bytes(4, "big")), ("2012", 1, 0, b"\x01")))
        self.assertEqual(result["items"]["5003"]["value"], -2.5)
        self.assertEqual(result["items"]["200b"]["value"], 0)

    def test_missing_or_false_flag_and_bad_status(self):
        without_flag = module.decode(frame(("3003", 3, 0, (900).to_bytes(4, "big"))))
        self.assertIsNone(without_flag["items"]["3003"]["value"])
        false_flag = module.decode(frame(("3003", 3, 0, (900).to_bytes(4, "big")), ("3004", 1, 0, b"\x00")))
        self.assertIsNone(false_flag["items"]["3003"]["value"])
        bad_status = module.decode(frame(("5003", 2, 1, (270).to_bytes(4, "big"))))
        self.assertIsNone(bad_status["items"]["5003"]["value"])

    def test_malformed_frame_rejected(self):
        valid = frame(("5003", 2, 0, (270).to_bytes(4, "big")))
        for broken in (valid[:-1], valid + b"\x00", valid[:3] + b"\x02" + valid[4:]):
            with self.assertRaises(ValueError):
                module.decode(broken)


if __name__ == "__main__":
    unittest.main()
