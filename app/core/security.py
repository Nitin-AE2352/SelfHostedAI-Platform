
import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import settings


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    """Password ko salted PBKDF2 hash mein convert karo."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{_b64encode(salt)}${_b64encode(digest)}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Submitted password ko stored hash ke saath verify karo."""
    try:
        algorithm, iterations, salt_text, digest_text = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = _b64decode(salt_text)
        expected = _b64decode(digest_text)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    value += "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))


def create_access_token(user: dict) -> str:
    """HS256-signed access token banao."""
    now = int(time.time())

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + settings.access_token_minutes * 60,
    }

    encoded_header = _b64encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    return f"{encoded_header}.{encoded_payload}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    """Token signature aur expiry verify karo."""
    try:
        header_text, payload_text, signature_text = token.split(".")

        header = json.loads(_b64decode(header_text))
        payload = json.loads(_b64decode(payload_text))

        if header.get("alg") != "HS256":
            return None

        signing_input = f"{header_text}.{payload_text}".encode("ascii")
        expected_signature = hmac.new(
            settings.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        actual_signature = _b64decode(signature_text)

        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        if int(payload.get("exp", 0)) <= int(time.time()):
            return None

        if not payload.get("sub"):
            return None

        return payload

    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
