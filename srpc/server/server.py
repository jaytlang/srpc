from typing import Dict, Optional, Type
from types import TracebackType

from srpc.config.config import ServerConfig
from srpc.server.rpc_handler import RPCHandler
from srpc.ssl.ssl_context_builder import SSLContextBuilder
from srpc.server.rpc_server import RPCServer
from srpc.server.authenticator import Authenticator

class Server:
    def __init__(self, config: ServerConfig):
        ssl_context_builder = SSLContextBuilder(
            protocol=config.shared.ssl_version,
            keyfile=config.keyfile,
            certfile=config.shared.certfile
        )
        ssl_context = ssl_context_builder.build_server()
        rpc_configs = config.rpcs
        rpcs: Dict[int, RPCHandler] = {}
        for rpc_config in rpc_configs:
            rpc_id = rpc_config.rpc_id
            if rpc_id in rpcs:
                raise ValueError(f"Duplicated RPC ID: {rpc_id}")
            rpc_handler = RPCHandler(rpc_config)
            rpcs[rpc_id] = rpc_handler
        authenticator = Authenticator()
        self._server = RPCServer(
            config.shared.hostname,
            config.shared.port,
            ssl_context=ssl_context,
            authenticator=authenticator,
            rpcs=rpcs
        )

    async def serve(self) -> None:
        await self._server.serve()

    async def __aenter__(self) -> 'Server':
        await self.serve()
        return self

    async def close(self) -> None:
        await self._server.close()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        await self.close()
