import importlib.util
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "jwt_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
create_token = solution.create_token
decode = solution.decode
verify = solution.verify


def test_create_and_decode():
    payload = {"sub": "user1", "role": "admin"}
    token = create_token(payload, "secret123")
    result = decode(token)
    assert result["sub"] == "user1"
    assert result["role"] == "admin"


def test_create_and_verify():
    payload = {"sub": "user2"}
    token = create_token(payload, "mysecret", exp_seconds=600)
    result = verify(token, "mysecret")
    assert result["sub"] == "user2"
    assert "exp" in result
    assert "iat" in result


def test_verify_wrong_secret_raises():
    token = create_token({"sub": "user"}, "correct_secret")
    try:
        verify(token, "wrong_secret")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_verify_expired_token_raises():
    payload = {"sub": "user", "exp": int(time.time()) - 3600, "iat": int(time.time()) - 7200}
    token = create_token(payload, "secret", exp_seconds=1)
    # Force a token with past expiry by manually building it
    import json, base64
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    import hmac, hashlib
    sig = hmac.new(b"secret", f"{header}.{body}".encode(), hashlib.sha256)
    signature = base64.urlsafe_b64encode(sig.digest()).rstrip(b"=").decode()
    token = f"{header}.{body}.{signature}"
    try:
        verify(token, "secret")
        raise AssertionError("expected ValueError for expired token")
    except ValueError:
        pass


def test_decode_nested_payload():
    payload = {"sub": "user", "data": {"nested": True, "items": [1, 2, 3]}}
    token = create_token(payload, "secret")
    result = decode(token)
    assert result["data"]["nested"] is True
    assert result["data"]["items"] == [1, 2, 3]


def test_malformed_token_raises():
    try:
        decode("not.a.valid-token")
    except Exception:
        pass


def test_roundtrip_preserves_types():
    payload = {"num": 42, "flag": True, "nothing": None, "name": "test"}
    token = create_token(payload, "s")
    result = verify(token, "s")
    assert result["num"] == 42
    assert result["flag"] is True
    assert result["nothing"] is None


def test_tampered_payload_raises():
    token = create_token({"sub": "original"}, "secret")
    parts = token.split(".")
    import json, base64
    payload_data = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    payload_data["sub"] = "tampered"
    parts[1] = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).rstrip(b"=").decode()
    tampered = ".".join(parts)
    try:
        verify(tampered, "secret")
        raise AssertionError("expected ValueError for tampered token")
    except ValueError:
        pass


def test_token_has_three_parts():
    token = create_token({"sub": "x"}, "s")
    assert len(token.split(".")) == 3


def test_different_payloads_different_tokens():
    t1 = create_token({"sub": "a"}, "s")
    t2 = create_token({"sub": "b"}, "s")
    assert t1 != t2


def test_different_secrets_different_signatures():
    token = create_token({"sub": "a"}, "secret1")
    parts = token.split(".")
    token2 = create_token({"sub": "a"}, "secret2")
    parts2 = token2.split(".")
    assert parts[2] != parts2[2]
