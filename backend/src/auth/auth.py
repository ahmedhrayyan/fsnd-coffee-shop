import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev22.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drink'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must starts with Bearer.'
        }, 401)

    if len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)

    if len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization Header must be Bearer token.'
        }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'Unauthorized',
            'description': 'You don\'t have access to this resource'
        }, 403)

    return True


def verify_decode_jwt(token):
    jsonurl = urlopen('https://'+AUTH0_DOMAIN+'/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://'+AUTH0_DOMAIN+'/'
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token is expired.'
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'incorrect_claims',
                'description': 'Incorrect claims,'
                ' please check audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication.'
            }, 401)

        _request_ctx_stack.top.current_user = payload

    else:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Unable to find appropriate key'
        }, 401)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            verify_decode_jwt(token)
            ctx = _request_ctx_stack.top
            check_permissions(permission, ctx.current_user)
            return f(*args, **kwargs)

        return wrapper
    return requires_auth_decorator
