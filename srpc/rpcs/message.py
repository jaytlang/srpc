import struct
import asyncio
from typing import NamedTuple

# Message format:
# 32 bits - RPC ID
# 32 bits - payload length
# Variable length - payload

class Message(NamedTuple):
    rpc_id: int
    request_id: int
    data: bytes

Q_SIZE = struct.calcsize("Q")
BITS_PER_BYTE = 8
Q_MIN = 0
Q_MAX = 2 ** (Q_SIZE * BITS_PER_BYTE) - 1

def encode_message(message: Message) -> bytes:
    rpc_id = message.rpc_id
    request_id = request_id = message.request_id
    data = message.data
    assert rpc_id >= Q_MIN
    assert rpc_id <= Q_MAX
    assert request_id >= Q_MIN
    assert request_id <= Q_MAX
    data_len = len(data)
    return struct.pack(f"!QQQ{data_len}s", rpc_id, request_id, len(data), data)

async def decode_message(reader: asyncio.StreamReader) -> Message:
    header_bytes = await reader.readexactly(3 * Q_SIZE)
    rpc_id, request_id, payload_length = struct.unpack("!QQQ", header_bytes)
    data_bytes = await reader.readexactly(payload_length)
    data, = struct.unpack(f"!{payload_length}s", data_bytes)
    return Message(rpc_id=rpc_id, request_id=request_id, data=data)
