from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "StrongPassword123!"
    saved_hash = hash_password(password)

    assert saved_hash != password
    assert verify_password(password, saved_hash)
    assert not verify_password("WrongPassword123!", saved_hash)


def test_token_round_trip():
    user = {"id": 7, "username": "localtest", "role": "user"}
    token = create_access_token(user)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "7"
    assert payload["username"] == "localtest"


def test_invalid_token_rejected():
    assert decode_access_token("not.a.valid-token") is None