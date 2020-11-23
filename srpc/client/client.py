import socket
import ssl
import time
import asyncio
import logging
from typing import Optional

from srpc.ssl.ssl_context_builder import SSLContextBuilder
from srpc.config.config import ClientConfig
from srpc.rpcs.authentication import create_auth_request, Credentials, parse_auth_response
from srpc.rpcs.message import Message, encode_message, decode_message

LOGGER = logging.getLogger(__name__)

class Client:
    def __init__(self, config: ClientConfig):
        self._ssl_context = SSLContextBuilder(config.shared.ssl_version, config.shared.certfile).build_client()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._address = config.shared.address
        self._port = config.shared.port
        self._request_id_to_response: Dict[int, Message] = {}
    
    async def connect(self) -> None:
        assert self._reader is None
        assert self._writer is None
        self._reader, self._writer = await asyncio.open_connection(host=self._address, port=self._port, ssl=self._ssl_context, )
    
    async def __aenter__(self) -> 'Client':
        await self.connect()
        return self


    async def close(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def rpc(self, message: Message) -> Message:
        assert self._writer is not None
        encoded_message = encode_message(message)
        self._writer.write(encode_message(message))
        await self._writer.drain()
        request_id = message.request_id
        while True:
            if request_id in self._request_id_to_response:
                response_message = self._request_id_to_response[request_id]
                del self._request_id_to_response[request_id]
                return response_message
            await asyncio.sleep(0)
    
    async def loop(self) -> None:
        while True:
            try:
                message = await decode_message(self._reader)
            except asyncio.IncompleteReadError:
                return
            LOGGER.debug("Received message: %s", message)
            self._request_id_to_response[message.request_id] = message
            await asyncio.sleep(0)

    async def run(self) -> None:
        auth_message = create_auth_request(1, Credentials("username", "password"))
        auth_response = await self.rpc(auth_message)
        rpcs = parse_auth_response(auth_response)
        for rpc in rpcs:
            print(f"RPC {rpc.rpc_id} - {rpc.rpc_name}")
        
        rpc_1_message = Message(rpc_id=1, request_id=0, data=b"hello, world 0")
        print("RPC 1 response")
        print(await self.rpc(rpc_1_message))

        rpc_2_message = Message(rpc_id=1, request_id=1, data=b"hello, world 1")
        print("RPC 2 response")
        print(await self.rpc(rpc_2_message))
