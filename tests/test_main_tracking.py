import argparse
import unittest
from unittest.mock import patch

from main import track_generated_application, validate_tracking_args


def tracking_args(
    track: bool = True,
    company: str = "Example Ltd",
    position: str = "Support Engineer",
    url: str = "https://example.com/job",
    notes: str = "Generated application",
) -> argparse.Namespace:
    return argparse.Namespace(
        track=track,
        company=company,
        position=position,
        url=url,
        notes=notes,
    )


class MainTrackingTests(unittest.TestCase):
    def test_validate_tracking_args_allows_disabled_tracking(self) -> None:
        args = tracking_args(track=False, company="", position="")

        validate_tracking_args(args)

    def test_validate_tracking_args_requires_company_when_tracking(self) -> None:
        args = tracking_args(company="")

        with self.assertRaises(ValueError):
            validate_tracking_args(args)

    def test_validate_tracking_args_requires_position_when_tracking(self) -> None:
        args = tracking_args(position="")

        with self.assertRaises(ValueError):
            validate_tracking_args(args)

    def test_track_generated_application_saves_generated_job(self) -> None:
        args = tracking_args()

        with patch("main.add_job", return_value=7) as add_job_mock:
            job_id = track_generated_application(args, "support")

        self.assertEqual(job_id, 7)
        add_job_mock.assert_called_once()
        _, kwargs = add_job_mock.call_args
        self.assertEqual(kwargs["company"], "Example Ltd")
        self.assertEqual(kwargs["position"], "Support Engineer")
        self.assertEqual(kwargs["role"], "support")
        self.assertEqual(kwargs["status"], "generated")

    def test_track_generated_application_returns_none_when_disabled(self) -> None:
        args = tracking_args(track=False)

        with patch("main.add_job") as add_job_mock:
            job_id = track_generated_application(args, "support")

        self.assertIsNone(job_id)
        add_job_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
