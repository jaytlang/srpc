import asyncio
import argparse
import os
import logging

from srpc.sdk.consumer import Consumer

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)

ECHO_RPC_ID = 1

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection_point", type=str, required=True)
    args = parser.parse_args()
    connection_point = args.connection_point
    consumer = Consumer(connection_point)

    asyncio.run(run_consumer(consumer))

async def run_consumer(consumer: Consumer) -> None:
    async with consumer:
        await consumer.connect()
        
        print("RPC 1 response")
        print(await consumer.rpc(ECHO_RPC_ID, b"hello, world 1"))

        print("RPC 2 response")
        print(await consumer.rpc(ECHO_RPC_ID, b"hello, world 2"))

if __name__ == "__main__":
    main()
