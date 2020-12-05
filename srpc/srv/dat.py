# Control file message structure
# These are ONLY used for communication through
# posted connections, not the actual files themselves

import ssl
import struct
import asyncio
import enum
from typing import NamedTuple, Dict

# Message format:
# 32 bits - RPC ID
# 32 bits - client-derived tag
# Variable length - 9P-like payload

class Message(NamedTuple):
    rpc: int
    tag: int
    data: bytes

class Con(NamedTuple):
    hostname: str
    port: int
    ssl: ssl.SSLContext


# SSL context helpers
# Again, largely taken from the original sRPC repo
#
# DELETEME: Designed under the assumption that SSL
# certificates are used to encrypt the connection before
# user authentication actually occurs. I think that's
# how this works. Authentication is an L7 problem.

from typing import Optional

class SSLContextBuilder:
    def __init__(self, protocol: int, certfile: str, keyfile: Optional[str] = None):
        self._certfile = certfile
        self._keyfile = keyfile
        self._protocol = protocol

    def build_server(self) -> ssl.SSLContext:
        context = ssl.SSLContext(self._protocol)
        context.load_cert_chain(certfile=self._certfile, keyfile=self._keyfile)
        return context
