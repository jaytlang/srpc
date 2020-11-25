import argparse
import ssl
from typing import Optional, List
import asyncio
import logging
import os

from srpc.client.client import Client
from srpc.config.config import ClientConfig, SharedConfig

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

def connect() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostname", type=str, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--certfile", type=str, required=True)
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, required=True)
    parser.add_argument("--connection_point", type=str, required=True)
    parser.add_argument("rpcs", type=int, nargs="*", help="RPCs to allow access to (blank for all)")
    args = parser.parse_args()
    rpcs: Optional[List[int]] = None
    if len(args.rpcs) > 0:
        rpcs = args.rpcs
    client_config = ClientConfig(
        shared=SharedConfig(
            hostname=args.hostname,
            port=args.port,
            certfile=args.certfile,
            ssl_version=ssl.PROTOCOL_TLSv1_2
        ),
        socket_filepath=args.connection_point,
        username=args.username,
        password=args.password,
        rpcs=rpcs
    )

    async def run_client() -> None:
        async with Client(client_config) as client:
            await client.connect()
            await client.spin()
    asyncio.run(run_client())

if __name__ == "__main__":
    connect()
