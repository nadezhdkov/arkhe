from datetime import datetime, timedelta
from typing import Any, Optional


class JwtService:
    """
    JWT token creation and verification.

    Requires PyJWT::

        pip install PyJWT
    """

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        expiry_minutes: int = 60,
    ):
        self._secret = secret
        self._algorithm = algorithm
        self._expiry = timedelta(minutes=expiry_minutes)

    def encode(self, payload: dict) -> str:
        try:
            import jwt
        except ImportError:
            raise ImportError("PyJWT is required: pip install PyJWT")
        data = dict(payload)
        data["exp"] = datetime.utcnow() + self._expiry
        return jwt.encode(data, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> Optional[dict]:
        try:
            import jwt
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except ImportError:
            raise ImportError("PyJWT is required: pip install PyJWT")
        except Exception:
            return None

    def is_valid(self, token: str) -> bool:
        return self.decode(token) is not None
