import argparse
import unittest
from pathlib import Path
from unittest.mock import patch

from config import OUTPUTS_DIR
from main import (
    get_output_dir,
    slugify,
    track_generated_application,
    validate_tracking_args,
)


def tracking_args(
    track: bool = True,
    company: str = "Example Ltd",
    position: str = "Support Engineer",
    url: str = "https://example.com/job",
    notes: str = "Generated application",
    output_dir: Path | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        track=track,
        company=company,
        position=position,
        url=url,
        notes=notes,
        output_dir=output_dir,
    )


class MainTrackingTests(unittest.TestCase):
    def test_get_output_dir_uses_default_when_not_provided(self) -> None:
        args = tracking_args(track=False, output_dir=None)

        self.assertEqual(get_output_dir(args), OUTPUTS_DIR)

    def test_get_output_dir_uses_custom_path_when_provided(self) -> None:
        custom_output_dir = Path("outputs/example-ltd-support-engineer")
        args = tracking_args(output_dir=custom_output_dir)

        self.assertEqual(get_output_dir(args), custom_output_dir)

    def test_get_output_dir_uses_company_and_position_when_tracking(self) -> None:
        args = tracking_args(
            company="Example Ltd",
            position="Support Engineer",
            output_dir=None,
        )

        self.assertEqual(
            get_output_dir(args),
            OUTPUTS_DIR / "example-ltd-support-engineer",
        )

    def test_slugify_creates_safe_folder_names(self) -> None:
        self.assertEqual(
            slugify("Junior Python Developer / APIs"),
            "junior-python-developer-apis",
        )

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
        self.assertEqual(
            kwargs["output_dir"],
            str(OUTPUTS_DIR / "example-ltd-support-engineer"),
        )

    def test_track_generated_application_returns_none_when_disabled(self) -> None:
        args = tracking_args(track=False)

        with patch("main.add_job") as add_job_mock:
            job_id = track_generated_application(args, "support")

        self.assertIsNone(job_id)
        add_job_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
