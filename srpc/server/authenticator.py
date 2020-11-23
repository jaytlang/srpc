from typing import NamedTuple
import json

from srpc.rpcs.message import Message
from srpc.rpcs.authentication import parse_auth_request

class AuthenticationFailedException(Exception):
    pass

class AuthenticatedClient(NamedTuple):
    security_context: object
    user_id: int

class Authenticator:
    def __init__(self):
        pass

    def authenticate_client(self, message: Message) -> AuthenticatedClient:
        credentials = parse_auth_request(message)
        # TODO get user id and security context from username and password.
        # Throw AuthenticationFailedException if appropriate
        # Values below are dummy
        return AuthenticatedClient(user_id=1000, security_context=1000)
