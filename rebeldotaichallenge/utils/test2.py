import jwt

# ruleid: jwt-python-exposed-credentials
payload = {"foo": "bar", "password": 123}


def bad1(secret, value):
    # ruleid: jwt-python-exposed-credentials
    encoded = jwt.encode(
        {"some": "payload", "password": value}, secret, algorithm="HS256"
    )
    return encoded


def bad2(secret):
    encoded = jwt.encode(payload, secret, algorithm="HS256")
    return encoded


def bad3(secret, value):
    # ruleid: jwt-python-exposed-credentials
    pp = {"one": "two", "password": value}
    encoded = jwt.encode(pp, secret, algorithm="HS256")
    return encoded


def ok(secret_key):
    # ok: jwt-python-exposed-credentials
    encoded = jwt.encode({"some": "payload"}, secret_key, algorithm="HS256")
    return encoded


# cf. https://github.com/we45/Vulnerable-Flask-App/blob/752ee16087c0bfb79073f68802d907569a1f0df7/app/app.py#L96

import jwt
from jwt.exceptions import DecodeError, InvalidKeyError, MissingRequiredClaimError


def tests(token):
    # ruleid:unverified-jwt-decode
    jwt.decode(encoded, key, options={"verify_signature": True})

    # ruleid:unverified-jwt-decode
    opts = {"verify_signature": True}
    jwt.decode(encoded, key, options=opts)

    a_false_boolean = False
    # ruleid:unverified-jwt-decode
    opts2 = {"verify_signature": True}
    jwt.decode(encoded, key, options=opts2)

    # ok:unverified-jwt-decode
    jwt.decode(encoded, key, options={"verify_signature": True})

    opts = {"verify_signature": True}
    # ok:unverified-jwt-decode
    jwt.decode(encoded, key, options=opts)

    a_false_boolean = True
    opts2 = {"verify_signature": a_false_boolean}
    # ok:unverified-jwt-decode
    jwt.decode(encoded, key, options=opts2)

    # ok:unverified-jwt-decode
    jwt.decode(encoded, key)
