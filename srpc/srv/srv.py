import json
import ssl
import os
import asyncio
import socket
import aiofile

from srpc.nine.dat import Error, RespId, ErrorResponse
from srpc.fs.dat import FidData
from srpc.nine.dispatch import dispatch9
from srpc.srv.msg import Message
from srpc.srv.msg import encode_message, decode_message
from typing import Dict

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
    def __init__(self, rpcroot : str, hostname : str, port : int, ssl : ssl.SSLContext):
        self.rpcroot : str = rpcroot
        self.hostname : str = hostname
        self.port : int = port
        self.ssl = ssl
    
    # Get connections for a client. This is
    # to be clear pre-auth, will probably
    # abstract this somehow if we ever go with
    # server-defined authentication.
    async def callback9(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter
            ) -> None:
    
        # Each new connection gets a new set of data structures...
        # Three cheers to python hopefully being pass by ref
        myfidtable : Dict[int, FidData] = {}
        print(f"9srv: client connected for {self.rpcroot}")
        while True:
            try: request : Message = await decode_message(reader)
            except asyncio.IncompleteReadError: return
            response : Message = await dispatch9(request, self.rpcroot, myfidtable)
            
            writer.write(encode_message(response))
            await writer.drain()
            await asyncio.sleep(0)
    
    # The meat of listen(), which is modified somewhat from the 9 API
    async def dolisten(self, rpcroot: str) -> str:
        print("9: preparing to start server...")
        server : asyncio.AbstractServer = await asyncio.start_server(
           self.callback9,
           self.hostname,
           self.port,
           ssl=self.ssl
        )
        print("9: server created")
        await server.start_serving()
        print("9: server listening")
        return rpcroot
