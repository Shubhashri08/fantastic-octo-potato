import unittest
from unittest.mock import MagicMock, patch

from app.event_output import get_event_output, severity_label


class TestEventOutput(unittest.TestCase):
    def test_severity_label_conversion(self):
        self.assertEqual(severity_label(1), "low")
        self.assertEqual(severity_label(2), "low")
        self.assertEqual(severity_label(3), "medium")
        self.assertEqual(severity_label(4), "high")
        self.assertEqual(severity_label(5), "high")

    @patch("app.event_output.SessionLocal")
    def test_get_event_output(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_event_row = MagicMock()
        mock_event_row._mapping = {
            "event_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "event_type": "ACCIDENT",
            "timestamp": "2026-08-16T05:00:00+00:00",
            "severity": 5,
            "source": "camera",
            "confidence": 0.91,
            "latitude": 19.076,
            "longitude": 72.8777,
        }

        mock_db.execute.return_value.fetchone.return_value = mock_event_row

        output = get_event_output("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

        self.assertEqual(output["event_id"], "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        self.assertEqual(output["event_type"], "ACCIDENT")
        self.assertEqual(output["severity"], "high")
        self.assertEqual(output["source"], "camera")
        self.assertEqual(output["confidence"], 0.91)
        self.assertEqual(output["latitude"], 19.076)
        self.assertEqual(output["longitude"], 72.8777)
        self.assertEqual(output["timestamp"], "2026-08-16T05:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
