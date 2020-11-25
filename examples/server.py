import ssl
import os
import asyncio
import logging

from srpc.config.config import ServerConfig, SharedConfig, RPCConfig
from srpc.server.server import Server

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

def main() -> None:
    server_config = ServerConfig(
        shared=SharedConfig(
            hostname="0.0.0.0",
            port=8000,
            certfile=os.path.join(os.path.dirname(__file__), "srpc.crt"),
            ssl_version=ssl.PROTOCOL_TLSv1_2
        ),
        keyfile=os.path.join(os.path.dirname(__file__), "srpc.key"),
        rpcs=[RPCConfig(
            filepath="/tmp/rpc.sock",
            rpc_id=1
        )]
    )
    server = Server(server_config)
    async def run_server() -> None:
        async with server:
            while True:
                await asyncio.sleep(0)
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
