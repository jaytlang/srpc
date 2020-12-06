import asyncio
import os
import sys

import aiofiles

from srpc.lib.srv import Srv

async def main() -> None:
    srv = Srv()
    await srv.ssl_context_helper(
        os.path.join(os.path.dirname(__file__), "srpc.crt"),
        os.path.join(os.path.dirname(__file__), "srpc.key"))
    await srv.announce("localhost", 42069, "/tmp/echo")

    async for linedir in srv.listen("/tmp/echo"):
        print(f"New linedir: {linedir}")
        loop = asyncio.get_event_loop()
        if linedir is not None:
            await echo(linedir)

async def echo(linedir: str) -> None:
    send = linedir + "/echo/send"
    recv = linedir + "/echo/recv"

    while True:
        async with aiofiles.open(recv, 'r') as rf:
            print("Got data out")
            data = await rf.read()
            async with aiofiles.open(send, 'w') as wf:
                await wf.write(data + "\n")

def main2() -> None:
    if os.getuid() != 0:
        print("Error: you should start the server as root!")
        sys.exit(1)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

if __name__ == "__main__":
    main2()
