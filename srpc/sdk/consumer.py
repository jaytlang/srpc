import asyncio
import logging
from typing import Dict, Optional, Tuple, Type
from types import TracebackType

from srpc.rpcs.message import Message, encode_message, decode_message

LOGGER = logging.getLogger(__name__)

class Consumer:
    def __init__(self, rpc_filepath: str) -> None:
        self._rpc_filepath = rpc_filepath
        self._rpc_to_request_id_counter: Dict[int, int] = {}
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._rpc_and_request_id_to_response: Dict[Tuple[int, int], Message] = {}
        self._loop_task: Optional[asyncio.Task[None]] = None

    async def setup(self) -> None:
        assert self._reader is None
        assert self._writer is None
        self._reader, self._writer = await asyncio.open_unix_connection(self._rpc_filepath)

    async def __aenter__(self) -> 'Consumer':
        await self.setup()
        return self

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
        if self._loop_task is not None:
            self._loop_task.cancel()
            while not self._loop_task.done():
                await asyncio.sleep(0)
            self._loop_task = None
        self._reader = None

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        await self.close()

    async def rpc(self, rpc_id: int, data: bytes) -> bytes:
        assert self._reader is not None
        assert self._writer is not None
        assert self._loop_task is not None
        if rpc_id not in self._rpc_to_request_id_counter:
            self._rpc_to_request_id_counter[rpc_id] = 0
        request_id = self._rpc_to_request_id_counter[rpc_id]
        rpc_and_request_id = rpc_id, request_id
        message = Message(rpc_id, request_id, data)
        self._writer.write(encode_message(message))
        await self._writer.drain()
        while True:
            await self._ensure_connected()
            if rpc_and_request_id in self._rpc_and_request_id_to_response:
                response_message = self._rpc_and_request_id_to_response[rpc_and_request_id]
                del self._rpc_and_request_id_to_response[rpc_and_request_id]
                assert rpc_id == response_message.rpc_id
                assert request_id == response_message.request_id
                return response_message.data
            await asyncio.sleep(0)

    async def _loop(self) -> None:
        assert self._reader is not None
        while True:
            try:
                message = await decode_message(self._reader)
            except asyncio.IncompleteReadError:
                await self.close()
                return
            LOGGER.debug("Received message: %s", message)
            self._rpc_and_request_id_to_response[message.rpc_id, message.request_id] = message
            await asyncio.sleep(0)

    async def connect(self) -> None:
        assert self._loop_task is None
        self._loop_task = asyncio.create_task(self._loop())

    async def _ensure_connected(self) -> None:
        assert self._writer is not None
        if self._writer.get_extra_info('socket') is None:
            raise RuntimeError("Connection Dropped")
