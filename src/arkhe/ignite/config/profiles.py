import os
from typing import Optional


class ProfileResolver:
    """
    Resolves the active Spring-style profile from the environment.
    Reads ``ARKHE_PROFILE`` (or ``SPRING_PROFILES_ACTIVE`` as fallback).
    """

    @staticmethod
    def resolve() -> Optional[str]:
        return (
            os.environ.get("ARKHE_PROFILE")
            or os.environ.get("SPRING_PROFILES_ACTIVE")
            or None
        )
