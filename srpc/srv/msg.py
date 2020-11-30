import asyncio
import struct
from srpc.srv.dat import Message

# Low level message encoding and decoding

Q_SIZE = struct.calcsize("Q")
BITS_PER_BYTE = 8
Q_MIN = 0
Q_MAX = 2 ** (Q_SIZE * BITS_PER_BYTE) - 1

def encode_message(message: Message) -> bytes:
    rpc = message.rpc
    tag = message.tag
    data = message.data
    assert rpc >= Q_MIN
    assert rpc <= Q_MAX
    assert tag >= Q_MIN
    assert tag <= Q_MAX
    data_len = len(data)
    return struct.pack(f"!QQQ{data_len}s", rpc, tag, len(data), data)

async def decode_message(reader: asyncio.StreamReader) -> Message:
    header_bytes = await reader.readexactly(3 * Q_SIZE)
    rpc, tag, payload_length = struct.unpack("!QQQ", header_bytes)
    data_bytes = await reader.readexactly(payload_length)
    data, = struct.unpack(f"!{payload_length}s", data_bytes)
    return Message(rpc=rpc, tag=tag, data=data)
