from srpc.lib.srv import *
import asyncio

async def main() -> None:
    await ssl_context_helper("srpc.crt", "srpc.key")
    await announce("localhost", 42069, "/home/jaytlang/test")
    await listen("/home/jaytlang/test")
    while True: await asyncio.sleep(0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
