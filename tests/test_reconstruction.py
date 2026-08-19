import unittest
from unittest.mock import MagicMock, patch

from app.reconstruction import reconstruct_event


class TestReconstruction(unittest.TestCase):
    @patch("app.reconstruction.SessionLocal")
    @patch("app.reconstruction.get_trajectory_with_movement")
    def test_reconstruct_event(self, mock_get_trajectory, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Event query mock response
        mock_event_row = MagicMock()
        mock_event_row._mapping = {
            "event_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "event_type": "ACCIDENT",
            "timestamp": "2026-08-16T05:00:00Z",
            "severity": 5,
        }

        # Entity query mock response
        mock_entity_row = MagicMock()
        mock_entity_row._mapping = {
            "track_id": "track_001",
            "entity_type": "PERSON",
            "association_type": "WITNESS",
            "proximity_meters": 15.27391664,
        }

        mock_db.execute.side_effect = [
            MagicMock(fetchone=lambda: mock_event_row),
            MagicMock(fetchall=lambda: [mock_entity_row]),
            MagicMock(),  # Update query
        ]

        mock_get_trajectory.return_value = [
            {
                "sighting_id": "S1",
                "track_id": "track_001",
                "camera_id": "CAM_A",
                "camera_name": "Camera A",
                "timestamp": "2026-08-16T04:58:00Z",
                "latitude": 19.0761,
                "longitude": 72.8778,
                "distance_from_previous_meters": None,
                "time_from_previous_seconds": None,
            },
            {
                "sighting_id": "S2",
                "track_id": "track_001",
                "camera_id": "CAM_C",
                "camera_name": "Camera C",
                "timestamp": "2026-08-16T05:01:00Z",
                "latitude": 19.0770,
                "longitude": 72.8785,
                "distance_from_previous_meters": 123.9041645,
                "time_from_previous_seconds": 180,
            },
            {
                "sighting_id": "S3",
                "track_id": "track_001",
                "camera_id": "CAM_A",
                "camera_name": "Camera A",
                "timestamp": "2026-08-16T05:05:00Z",
                "latitude": 19.0775,
                "longitude": 72.8790,
                "distance_from_previous_meters": 76.36932736,
                "time_from_previous_seconds": 240,
            },
        ]

        result = reconstruct_event("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

        self.assertIn("event", result)
        self.assertIn("entities", result)
        self.assertEqual(result["event"]["event_id"], "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        self.assertEqual(result["event"]["event_type"], "ACCIDENT")
        self.assertEqual(result["event"]["severity"], 5)
        self.assertEqual(len(result["entities"]), 1)

        entity = result["entities"][0]
        self.assertEqual(entity["track_id"], "track_001")
        self.assertEqual(entity["entity_type"], "PERSON")
        self.assertEqual(entity["association_type"], "WITNESS")
        self.assertEqual(entity["proximity_meters"], 15.27391664)
        self.assertEqual(len(entity["trajectory"]), 3)

        self.assertEqual(entity["trajectory"][0]["camera_name"], "Camera A")
        self.assertIsNone(entity["trajectory"][0]["distance_from_previous_meters"])

        self.assertEqual(entity["trajectory"][1]["camera_name"], "Camera C")
        self.assertEqual(entity["trajectory"][1]["distance_from_previous_meters"], 123.9041645)
        self.assertEqual(entity["trajectory"][1]["time_from_previous_seconds"], 180.0)

        self.assertEqual(entity["trajectory"][2]["camera_name"], "Camera A")
        self.assertEqual(entity["trajectory"][2]["distance_from_previous_meters"], 76.36932736)

        self.assertTrue(mock_db.commit.called)


if __name__ == "__main__":
    unittest.main()
