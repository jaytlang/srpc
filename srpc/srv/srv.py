import ssl
import asyncio
from multiprocessing import Manager
from typing import Dict, AsyncIterator, Optional

from srpc.fs.dat import FidData
from srpc.fs.qid import Qid
from srpc.nine.dispatch import dispatch9
from srpc.nine.dat import MessageType
from srpc.srv.dat import encode_message, decode_message

class RPCServer:
    """
    async def ctl_reader(ctl_fname: str) -> None:
        async with aiofile.AIOFile(ctl_fname + "/send", 'r') as f:
            async for line in aiofile.LineReader(f):
                if line == "close": continue
                else: continue
                asyncio.sleep(0)
            # TODO: stop the server in entirety
            # Then, exit out, since we can't rm a file
            # or directory created by root. This is handled
            # by preparecon
    """
    def __init__(self, rpcroot: str, hostname: str, port: int, ssl_context: ssl.SSLContext):
        self.rpcroot = rpcroot
        self.hostname = hostname
        self.port = port
        self.ssl_context = ssl_context
        self.newdata : Optional[str] = ""

    # Get connections for a client. This is
    # to be clear pre-auth, will probably
    # abstract this somehow if we ever go with
    # server-defined authentication.

    async def waitfordata(self) -> None:
        while not self.newdata:
            await asyncio.sleep(0)

    async def callback9(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:

        print(f"9srv: client connected for {self.rpcroot}")
        # Each new connection gets a new set of data structures...
        # Three cheers to python being pass by reference.

        # Additionally, wrap the dict so it's accessible across
        # processes. This way, for this connection, everyone holds
        # onto an up to date set of fids. Might not be totally
        # needed, but it's nice and comfy.
        mpmanager = Manager()
        myfidtable: Dict[int, FidData] = mpmanager.dict()
        myqid = Qid()

        # Do the thing
        while True:
            try:
                request = await decode_message(reader)
            except asyncio.IncompleteReadError:
                return
            response, linedir = await dispatch9(request, self.rpcroot, myfidtable, myqid, False)
            if response.message_type == MessageType.ATTACHR:
                self.newdata = linedir

            writer.write(encode_message(response))
            await writer.drain()
            await asyncio.sleep(0)

    # The meat of listen(), which is modified somewhat from the 9 API
    async def dolisten(self) -> AsyncIterator[Optional[str]]:
        print("9: preparing to start server...")
        server = await asyncio.start_server(
           self.callback9,
           self.hostname,
           self.port,
           ssl=self.ssl_context
        )
        print("9: server created")
        await server.start_serving()
        print("9: server listening")

        while True:
            await self.waitfordata()
            yield self.newdata
            self.newdata = ""
