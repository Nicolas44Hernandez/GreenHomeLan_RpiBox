"""Authentication management package"""
import jwt
import logging
from functools import wraps
from flask import  request, jsonify
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClientsRemoteAuth():
    secret_key: str

    @classmethod
    def set_secret_key(cls, secret_key:str):
        cls.secret_key = secret_key

    @classmethod
    def generate_token(cls, client_id:str):
        """Generate jwt token"""

        token = jwt.encode({
            'sub': client_id,
            'iat':datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=5)},
            ClientsRemoteAuth.secret_key,
            algorithm="HS256",
        )
        return token


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()

        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }

        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            jwt.decode(jwt=token, key=ClientsRemoteAuth.secret_key, algorithms="HS256")
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify
