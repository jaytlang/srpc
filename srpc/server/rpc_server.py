import ssl
import socketserver
import asyncio
import base64
import json
import logging
from typing import Type, Tuple, TypedDict, Mapping, List

from srpc.server.authenticator import AuthenticatedClient, AuthenticationFailedException, Authenticator
from srpc.rpcs.message import Message, decode_message, encode_message
from srpc.rpcs.authentication import create_auth_response, RPCDescriptor
from srpc.server.rpc_handler import RPCHandler

LOGGER = logging.getLogger(__name__)

class RPCServer:
    def __init__(self, address: str, port: int, ssl_context: ssl.SSLContext, authenticator: Authenticator, rpcs: Mapping[int, RPCHandler]) -> None:        
        self._address = address
        self._port = port
        self._authenticator = authenticator
        self._ssl_context = ssl_context
        self._rpcs = rpcs
        self._server: Optional[asyncio.AbstractServer] = None
    
    async def serve(self) -> None:
        assert self._server is None, "already serving"
        self._server = await asyncio.start_server(self.client_connected_cb, self._address, self._port, ssl=self._ssl_context)
        await self._server.start_serving()
    
    async def __aenter__(self) -> 'RPCServer':
        await self.serve()

    async def client_connected_cb(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            authentication_message = await decode_message(reader)            
            authenticated_client = self._authenticator.authenticate_client(authentication_message)
            available_rpcs: List[RPCDescriptor] = []
            for rpc_id, rpc_handler in self._rpcs.items():
                if rpc_handler.is_discoverable(authenticated_client):
                    available_rpcs.append(rpc_handler.rpc_descriptor)
            writer.write(encode_message(create_auth_response(authentication_message.request_id, available_rpcs)))
            await writer.drain()
            while True:
                try:
                    message = await decode_message(reader)
                except asyncio.IncompleteReadError:
                    return
                rpc_id = message.rpc_id
                if rpc_id not in self._rpcs:
                    LOGGER.error("Invalid RPC id: %d", rpc_id)
                    continue
                rpc_handler = self._rpcs[rpc_id]
                data = message.data
                request_id = message.request_id
                response_data = await rpc_handler.make_request(authenticated_client, message)
                response_message = Message(rpc_id, request_id, response_data)
                data_encoded = encode_message(response_message)
                writer.write(data_encoded)
                await writer.drain()
                await asyncio.sleep(0)
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def close(self) -> None:
        assert self._server is not None, "not serving"
        self._server.close()
        await self._server.wait_closed()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
