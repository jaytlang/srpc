from srpc.lib.srv import *
import asyncio
import os

async def main() -> None:
    await ssl_context_helper("srpc.crt", "srpc.key")
    await announce("localhost", 42069, "/home/notthensa/test")
    await listen("/home/notthensa/test")
    while True: await asyncio.sleep(0)

if(os.getuid() != 0):
    print("Error: you should start the server as root!")
    exit()
else:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
