import json
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import status_service  # noqa: E402


class StatusServiceTest(unittest.TestCase):
    def test_build_status_shape(self):
        payload = status_service.build_status()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("service", payload)
        self.assertIn("version", payload)
        self.assertIn("uptimeSec", payload)
        self.assertIn("timestamp", payload)
        self.assertTrue(isinstance(payload["uptimeSec"], float))
        datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))

    def test_json_serializable(self):
        payload = status_service.build_status()
        encoded = json.dumps(payload)
        self.assertIn('"status": "ok"', encoded)


if __name__ == "__main__":
    unittest.main()
