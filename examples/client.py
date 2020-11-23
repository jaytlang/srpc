import ssl
import os
import asyncio

from srpc.config.config import ClientConfig, SharedConfig
from srpc.client.client import Client

def main():
    client_config = ClientConfig(
        shared=SharedConfig(
            address="127.0.0.1",
            port=8000,
            certfile=os.path.join(os.path.dirname(__file__), "srpc.crt"),
            ssl_version=ssl.PROTOCOL_TLSv1_2
        ),
    )
    client = Client(client_config)
    async def run_client():
        async with client:
            asyncio.ensure_future(client.loop())
            await client.run()
    asyncio.run(run_client())

if __name__ == "__main__":
    main()
