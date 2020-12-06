import asyncio
from typing import Optional, Type
from types import TracebackType

from srpc.nine.dat import AuthRequest, AttachRequest, WalkRequest, \
    StatRequest, AppendRequest, ClunkRequest, RPCException
from srpc.lib.client import Client

class Cli:
    def __init__(self, certfile: str, hostname: str, port: int) -> None:
        self._client = Client(certfile, hostname, port)

    async def setup(self) -> None:
        await self._client.setup()

    async def __aenter__(self) -> 'Cli':
        await self.setup()
        return self

    async def close(self) -> None:
        await self._client.close()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        await self.close()

    async def parse9(self, intxt: str) -> None:
        splitinput = intxt.split()
        cmd = splitinput[0]
        if cmd == "auth":
            authafid = int(splitinput[1])
            uname = splitinput[2]
            aname = splitinput[3]
            authreq = AuthRequest(authafid, uname, aname)
            print(f"\t> {authreq}")
            authresp = await self._client.auth(authreq)
            print(f"\t< {authresp}")
            return

        if cmd == "attach":
            attafid = int(splitinput[1])
            attfid = int(splitinput[2])
            uname = splitinput[3]
            aname = splitinput[4]
            attreq = AttachRequest(attafid, attfid, uname, aname)
            print(f"\t> {attreq}")
            attresp = await self._client.attach(attreq)
            print(f"\t< {attresp}")
            return

        if cmd == "walk":
            walkfid = int(splitinput[1])
            walknfid = int(splitinput[2])
            path = splitinput[3]
            walkreq = WalkRequest(walkfid, walknfid, path)
            print(f"\t> {walkreq}")
            walkresp = await self._client.walk(walkreq)
            print(f"\t< {walkresp}")
            return

        if cmd == "stat":
            statfid = int(splitinput[1])
            statreq = StatRequest(statfid)
            print(f"\t> {statreq}")
            statresp = await self._client.stat(statreq)
            print(f"\t< {statresp}")
            return

        if cmd == "append":
            wrfid = int(splitinput[1])
            data = splitinput[2]
            writereq = AppendRequest(wrfid, data)
            print(f"\t> {writereq}")
            appendresp = await self._client.append(writereq)
            print(f"\t< {appendresp}")
            return

        if cmd == "clunk":
            clfid = int(splitinput[1])
            clunkreq = ClunkRequest(clfid)
            print(f"\t> {clunkreq}")
            clunkresp = await self._client.clunk(clunkreq)
            print(f"\t< {clunkresp}")
            return

        raise ValueError("Invalid command: " + cmd)

# This is just a test. Connect to some
# fixed server/port:
async def main() -> None:
    srv_address = "localhost"
    srv_port = 42069
    cert = "srpc.crt"

    print("Connected. The shell is yours.")
    async with Cli(cert, srv_address, srv_port) as cli:
        while True:
            cmd = input("% ")
            try:
                await cli.parse9(cmd)
            except (ValueError, TypeError, RPCException) as ex:
                print(ex)
                continue            
            await asyncio.sleep(0)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
