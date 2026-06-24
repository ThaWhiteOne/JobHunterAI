from pathlib import Path

from config import MASTER_PROFILE_PATH, ROLE_PROFILE_MAP
from file_utils import read_text_file


def select_profile(role: str) -> tuple[str, Path, bool]:
    profile_path = ROLE_PROFILE_MAP.get(role, MASTER_PROFILE_PATH)
    profile = read_text_file(profile_path, required=False)

    used_fallback = False
    if not profile:
        profile = read_text_file(MASTER_PROFILE_PATH, required=True)
        profile_path = MASTER_PROFILE_PATH
        used_fallback = True

    return profile, profile_path, used_fallback
