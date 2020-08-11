from flask import request, abort, make_response, jsonify
from functools import wraps
from app.utils import authorized_roles
from app import app
import datetime
import jwt
import os


active_tokens = []


def protected_endpoint(
    permitted_roles=authorized_roles, return_role=False, return_id=False,
):
    def decorator(func):
        @wraps(func)
        def authorize(*args, **kwargs):
            if kwargs is None:
                kwargs = {}
            if not os.getenv("TESTING", 0):
                auth_token = request.headers.get("Authorization")
                user_id, role = decode_auth_token(auth_token)
                if role not in permitted_roles:
                    abort(make_response(jsonify(error="Invalid permissions"), 403))
                else:
                    if return_id:
                        kwargs.update(
                            {"user_id": user_id,}
                        )
                    if return_role:
                        kwargs.update({"role": role})
                    return func(*args, **kwargs)
            else:
                if return_id:
                    kwargs.update({"user_id": "admin@dewa.com"})
                if return_role:
                    kwargs.update({"role": "general-manager"})
                return func(*args, **kwargs)

        return authorize

    return decorator


def encode_auth_token(user_id, role):
    """
    Generates the Auth Token
    :return: string
    """
    try:
        payload = {
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=0, seconds=(12 * 60 * 60)),  # 12 hours
            "iat": datetime.datetime.utcnow(),
            "sub": user_id,
            "role": role,
        }
        return jwt.encode(payload, os.getenv("AUTH_SECRET"), algorithm="HS256").decode(
            "utf-8"
        )
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    """Decodes the auth token.

    :param auth_token:
    :return: integer|string
    """
    try:
        if auth_token in active_tokens:
            payload = jwt.decode(auth_token, os.getenv("AUTH_SECRET"))
            return payload["sub"], payload["role"]
        raise jwt.InvalidTokenError
    except jwt.ExpiredSignatureError:
        token_index = active_tokens.index(auth_token)
        del active_tokens[token_index]
        abort(make_response(jsonify(error="TOKEN EXPIRED"), 401))
    except jwt.InvalidTokenError:
        abort(make_response(jsonify(error="TOKEN INVALID"), 401))

