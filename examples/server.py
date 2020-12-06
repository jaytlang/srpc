import asyncio
import os
import sys

from srpc.lib.srv import Srv

async def main() -> None:
    srv = Srv()
    await srv.ssl_context_helper(
        os.path.join(os.path.dirname(__file__), "srpc.crt"),
        os.path.join(os.path.dirname(__file__), "srpc.key"))
    await srv.announce("localhost", 42069, "/home/notthensa/test")
    await srv.listen("/home/notthensa/test")
    while True:
        await asyncio.sleep(0)

if __name__ == "__main__":
    if os.getuid() != 0:
        print("Error: you should start the server as root!")
        sys.exit(1)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
