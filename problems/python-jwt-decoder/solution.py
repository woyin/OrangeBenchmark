import base64
import hashlib
import hmac
import json
import time


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(payload: dict, secret: str, exp_seconds: int = 3600) -> str:
    return ""


def decode(token: str) -> dict:
    return {}


def verify(token: str, secret: str) -> dict:
    return {}
