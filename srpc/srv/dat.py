# Control file message structure
# These are ONLY used for communication through
# posted connections, not the actual files themselves

import ssl
from typing import NamedTuple, Optional
import asyncio
import struct

from srpc.nine.dat import MessageType


# Message format:
# 32 bits - RPC ID
# 32 bits - client-derived tag
# Variable length - 9P-like payload

class Message(NamedTuple):
    message_type: MessageType
    tag: int
    data: bytes

class Con(NamedTuple):
    hostname: str
    port: int
    ssl: ssl.SSLContext


Q_SIZE = struct.calcsize("Q")
I_SIZE = struct.calcsize("i")
BITS_PER_BYTE = 8
Q_MIN = 0
Q_MAX = 2 ** (Q_SIZE * BITS_PER_BYTE) - 1

def encode_message(message: Message) -> bytes:
    message_type = message.message_type.value
    tag = message.tag
    data = message.data
    assert tag >= Q_MIN
    assert tag <= Q_MAX
    data_len = len(data)
    return struct.pack(f"!iQQ{data_len}s", message_type, tag, len(data), data)

async def decode_message(reader: asyncio.StreamReader) -> Message:
    header_bytes = await reader.readexactly(I_SIZE + Q_SIZE + Q_SIZE)
    message_type_id, tag, payload_length = struct.unpack("!iQQ", header_bytes)
    data_bytes = await reader.readexactly(payload_length)
    data, = struct.unpack(f"!{payload_length}s", data_bytes)
    message_type = MessageType(message_type_id)
    return Message(message_type, tag, data)


# SSL context helpers
# Again, largely taken from the original sRPC repo
#
# DELETEME: Designed under the assumption that SSL
# certificates are used to encrypt the connection before
# user authentication actually occurs. I think that's
# how this works. Authentication is an L7 problem.

PROTOCOL = ssl.PROTOCOL_TLSv1_2

class SSLContextBuilder:
    def __init__(self, certfile: str, keyfile: Optional[str] = None):
        self._certfile = certfile
        self._keyfile = keyfile

    def build_server(self) -> ssl.SSLContext:
        context = ssl.SSLContext(PROTOCOL)
        context.load_cert_chain(certfile=self._certfile, keyfile=self._keyfile)
        return context

    def build_client(self) -> ssl.SSLContext:
        context = ssl.SSLContext(PROTOCOL)
        context.load_verify_locations(self._certfile)
        context.verify_mode = ssl.CERT_REQUIRED
        return context
