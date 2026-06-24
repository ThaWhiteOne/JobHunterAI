import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from profile_selector import select_profile


class ProfileSelectorTests(unittest.TestCase):
    def test_selects_role_profile_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_profile = temp_path / "master_profile.md"
            developer_profile = temp_path / "developer_cv.md"
            master_profile.write_text("Master profile", encoding="utf-8")
            developer_profile.write_text("Developer profile", encoding="utf-8")

            with patch("profile_selector.MASTER_PROFILE_PATH", master_profile), patch(
                "profile_selector.ROLE_PROFILE_MAP",
                {"developer": developer_profile},
            ):
                profile, profile_path, used_fallback = select_profile("developer")

            self.assertEqual(profile, "Developer profile")
            self.assertEqual(profile_path, developer_profile)
            self.assertFalse(used_fallback)

    def test_falls_back_to_master_profile_when_role_profile_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_profile = temp_path / "master_profile.md"
            developer_profile = temp_path / "developer_cv.md"
            master_profile.write_text("Master profile", encoding="utf-8")
            developer_profile.write_text("", encoding="utf-8")

            with patch("profile_selector.MASTER_PROFILE_PATH", master_profile), patch(
                "profile_selector.ROLE_PROFILE_MAP",
                {"developer": developer_profile},
            ):
                profile, profile_path, used_fallback = select_profile("developer")

            self.assertEqual(profile, "Master profile")
            self.assertEqual(profile_path, master_profile)
            self.assertTrue(used_fallback)

    def test_falls_back_to_master_profile_when_role_profile_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_profile = temp_path / "master_profile.md"
            missing_profile = temp_path / "missing_cv.md"
            master_profile.write_text("Master profile", encoding="utf-8")

            with patch("profile_selector.MASTER_PROFILE_PATH", master_profile), patch(
                "profile_selector.ROLE_PROFILE_MAP",
                {"developer": missing_profile},
            ):
                profile, profile_path, used_fallback = select_profile("developer")

            self.assertEqual(profile, "Master profile")
            self.assertEqual(profile_path, master_profile)
            self.assertTrue(used_fallback)


if __name__ == "__main__":
    unittest.main()
