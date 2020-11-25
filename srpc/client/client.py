import asyncio
import struct
import logging
import os
from typing import Optional, Dict, Type
from types import TracebackType

from srpc.ssl.ssl_context_builder import SSLContextBuilder
from srpc.config.config import ClientConfig
from srpc.rpcs.authentication import create_auth_request, Credentials, parse_auth_response
from srpc.rpcs.message import Message, encode_message, decode_message

LOGGER = logging.getLogger(__name__)

CONSUMER_ID_BITS = 8
BITS_PER_BYTE = 8
Q_SIZE = struct.calcsize("Q")
CONSUMER_ID_OFFSET = Q_SIZE * BITS_PER_BYTE - CONSUMER_ID_BITS

class Client:
    def __init__(self, config: ClientConfig):
        ssl_context_builder = SSLContextBuilder(config.shared.ssl_version, config.shared.certfile)
        self._ssl_context = ssl_context_builder.build_client()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._socket: Optional[asyncio.AbstractServer] = None
        self._socket_filepath = config.socket_filepath
        self._authorized_rpcs = None if config.rpcs is None else frozenset(config.rpcs)
        self._hostname = config.shared.hostname
        self._port = config.shared.port
        self._username = config.username
        self._password = config.password
        self._request_id_to_response: Dict[int, Optional[Message]] = {}
        self._consumer_id_counter = 0
        self._loop_task: Optional[asyncio.Task[None]] = None

    async def setup(self) -> None:
        assert self._reader is None
        assert self._writer is None
        assert self._socket is None
        assert self._loop_task is None
        self._reader, self._writer = await asyncio.open_connection(
            self._hostname,
            self._port,
            ssl=self._ssl_context
        )
        try:
            os.remove(self._socket_filepath)
        except FileNotFoundError:
            pass
        self._socket = await asyncio.start_unix_server(
            self._client_connected_cb,
            self._socket_filepath
        )

    async def __aenter__(self) -> 'Client':
        await self.setup()
        return self

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
        if self._socket is not None:
            self._socket.close()
            await self._socket.wait_closed()
            self._socket = None
        if self._loop_task is not None:
            self._loop_task.cancel()
            while not self._loop_task.done():
                await asyncio.sleep(0)
            self._loop_task = None
        self._reader = None
        self._consumer_id_counter = 0

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        await self.close()

    async def rpc(self, consumer_id: int, message: Message) -> Message:
        assert self._writer is not None
        assert consumer_id >= 0
        assert consumer_id < 2**CONSUMER_ID_BITS
        request_id = message.request_id
        assert request_id >= 0
        assert request_id < 2**CONSUMER_ID_OFFSET
        request_id |= (consumer_id << CONSUMER_ID_OFFSET)
        assert request_id not in self._request_id_to_response, "duplicate request id"
        self._request_id_to_response[request_id] = None
        request_message = Message(
            rpc_id=message.rpc_id,
            request_id=request_id,
            data=message.data
        )
        LOGGER.info(
            "calling rpc_id(%d) request_id(%d) data(%s)",
            message.rpc_id,
            request_id,
            message.data
        )
        self._writer.write(encode_message(request_message))
        await self._writer.drain()
        while True:
            if self._request_id_to_response[request_id] is not None:
                response_message = self._request_id_to_response[request_id]
                assert response_message is not None
                del self._request_id_to_response[request_id]
                assert response_message.rpc_id == message.rpc_id
                LOGGER.info(
                    "responding rpc_id(%d) request_id(%d) data(%s)",
                    message.rpc_id,
                    request_id,
                    response_message.data
                )
                return Message(
                    rpc_id=response_message.rpc_id,
                    request_id=message.request_id,
                    data=response_message.data
                )
            await asyncio.sleep(0)

    async def _process_message(
        self,
        message: Message,
        consumer_id: int,
        writer: asyncio.StreamWriter
    ) -> None:
        if self._authorized_rpcs is not None:
            if message.rpc_id not in self._authorized_rpcs:
                raise RuntimeError("This RPC is not allowed")
        response = await self.rpc(consumer_id, message)
        writer.write(encode_message(response))
        await writer.drain()
        await asyncio.sleep(0)

    async def _client_connected_cb(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        # called when a new consumer connects to the socket file
        consumer_id = self._consumer_id_counter
        self._consumer_id_counter += 1

        while True:
            try:
                message = await decode_message(reader)
            except asyncio.IncompleteReadError:
                writer.close()
                await writer.wait_closed()
                return
            else:
                asyncio.create_task(self._process_message(message, consumer_id, writer))
                await asyncio.sleep(0)

    async def _loop(self) -> None:
        # Gets messages from the server and passes them to appropriate consumer
        assert self._socket is not None
        assert self._reader is not None
        assert self._writer is not None
        while True:
            try:
                message = await decode_message(self._reader)
            except asyncio.IncompleteReadError:
                return
            LOGGER.debug("Received message: %s", message)
            self._request_id_to_response[message.request_id] = message
            await asyncio.sleep(0)

    async def connect(self) -> None:
        assert self._loop_task is None
        self._loop_task = asyncio.create_task(self._loop())
        auth_message = create_auth_request(0, Credentials(self._username, self._password))
        auth_response = await self.rpc(consumer_id=self._consumer_id_counter, message=auth_message)
        rpcs = parse_auth_response(auth_response)
        print(f"Connected to {self._hostname}:{self._port}")
        for rpc in rpcs:
            print(f"RPC {rpc.rpc_id}: {rpc.rpc_name}")
        self._consumer_id_counter += 1

    async def spin(self) -> None:
        assert self._writer is not None
        while True:
            if self._writer.get_extra_info('socket') is None:
                raise RuntimeError("Connection Dropped")
            await asyncio.sleep(0)
