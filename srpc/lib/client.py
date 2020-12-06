import asyncio
import logging
import json
from typing import Optional, Dict, Type, TypeVar
from types import TracebackType

from srpc.srv.dat import Message, SSLContextBuilder, encode_message, decode_message
from srpc.nine.dat import MessageType, AuthRequest, AuthResponse, AttachRequest, AttachResponse, \
    WalkRequest, WalkResponse, StatRequest, StatResponse, AppendRequest, AppendResponse, \
    ClunkRequest, ClunkResponse, RPCException, Error

LOGGER = logging.getLogger(__name__)

ResponseMessage = TypeVar("ResponseMessage")

class Client:
    def __init__(self, certfile: str, hostname: str, port: int):
        ssl_context_builder = SSLContextBuilder(certfile)
        self._ssl_context = ssl_context_builder.build_client()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._hostname = hostname
        self._port = port
        self._tag = 0
        self._tag_to_response: Dict[int, Optional[Message]] = {}
        self._loop_task: Optional[asyncio.Task[None]] = None

    async def setup(self) -> None:
        assert self._reader is None
        assert self._writer is None
        assert self._loop_task is None
        self._reader, self._writer = await asyncio.open_connection(
            self._hostname,
            self._port,
            ssl=self._ssl_context
        )
        self._loop_task = asyncio.create_task(self._loop())
        print(f"Connected to {self._hostname}:{self._port}")

    async def __aenter__(self) -> 'Client':
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

    async def _rpc_wrapper(
        self,
        request: object,
        request_message_type: MessageType,
        response_message_cls: Type[ResponseMessage]
    ) -> ResponseMessage:
        tag = self._tag
        self._tag += 1
        request_bytes = json.dumps(request._asdict()).encode('utf-8') # type: ignore[attr-defined]
        request_message = Message(request_message_type, tag, request_bytes)
        response_message = await self._rpc(request_message)
        data_json = json.loads(response_message.data)
        # response message types are 1 more than the request type, by convention
        if response_message.message_type == MessageType(request_message_type.value + 1):
            return response_message_cls(**data_json)  # type: ignore
        if response_message.message_type == MessageType.ERROR:
            raise RPCException(Error(data_json['errno']))
        raise ValueError("Invalid response_message from the server", response_message)

    async def auth(self, request: AuthRequest) -> AuthResponse:
        return await self._rpc_wrapper(request, MessageType.AUTH, AuthResponse)

    async def attach(self, request: AttachRequest) -> AttachResponse:
        return await self._rpc_wrapper(request, MessageType.ATTACH, AttachResponse)

    async def walk(self, request: WalkRequest) -> WalkResponse:
        return await self._rpc_wrapper(request, MessageType.WALK, WalkResponse)

    async def stat(self, request: StatRequest) -> StatResponse:
        return await self._rpc_wrapper(request, MessageType.STAT, StatResponse)

    async def append(self, request: AppendRequest) -> AppendResponse:
        return await self._rpc_wrapper(request, MessageType.APPEND, AppendResponse)

    async def clunk(self, request: ClunkRequest) -> ClunkResponse:
        return await self._rpc_wrapper(request, MessageType.CLUNK, ClunkResponse)

    async def _rpc(self, message: Message) -> Message:
        assert self._writer is not None
        tag = message.tag
        assert tag not in self._tag_to_response, "duplicate request id"
        self._tag_to_response[tag] = None
        request_message = Message(
            message_type=message.message_type,
            tag=tag,
            data=message.data
        )
        LOGGER.info(
            "calling message_type(%d) tag(%d) data(%s)",
            message.message_type,
            message.tag,
            message.data
        )
        self._writer.write(encode_message(request_message))
        await self._writer.drain()
        while True:
            if self._tag_to_response[tag] is not None:
                response_message = self._tag_to_response[tag]
                assert response_message is not None
                del self._tag_to_response[tag]
                assert response_message.tag == message.tag
                LOGGER.info(
                    "responding rpc_id(%d) tag(%d) data(%s)",
                    message.message_type,
                    tag,
                    response_message.data
                )
                return response_message
            await asyncio.sleep(0)

    async def _loop(self) -> None:
        # Gets messages from the server and passes them to appropriate consumer
        assert self._reader is not None
        assert self._writer is not None
        while True:
            try:
                message = await decode_message(self._reader)
            except asyncio.IncompleteReadError:
                return
            LOGGER.debug("Received message: %s", message)
            self._tag_to_response[message.tag] = message
            await asyncio.sleep(0)

    async def spin(self) -> None:
        assert self._writer is not None
        while True:
            if self._writer.get_extra_info('socket') is None:
                raise RuntimeError("Connection Dropped")
            await asyncio.sleep(0)
