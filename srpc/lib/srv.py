# High level server API

from typing import Dict, AsyncIterator, Optional
import os
import ssl
import shutil

from srpc.srv.srv import RPCServer
from srpc.srv.dat import Con

class Srv:
    def __init__(self) -> None:
        self._context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self._ctls: Dict[str, Con] = {}

    # Configure the ssl context automatically, for ease of use
    async def ssl_context_helper(self, certfile: str, keyfile: str) -> None:
        self._context.load_cert_chain(certfile = certfile, keyfile = keyfile)

    async def announce(self, hostname: str, port: int, rpcroot: str) -> None:
        newcon = Con(hostname, port, self._context)
        if rpcroot in self._ctls.keys():
            raise RuntimeError("ERROR: dir already announced")
        self._ctls[rpcroot] = newcon

        # Make necessary control structures
        os.makedirs("/srv", exist_ok=True)
        shutil.rmtree("/srv/ctl", ignore_errors=True)
        os.mkdir("/srv/ctl/")
        os.chmod("/srv/ctl/", 0o777)

        # All good. ctl/ gets populated when
        # new connections pop open - for now,
        # per unix user for simplicity. This is
        # an effective simplifying assumption,
        # but one that deviates from the 9P
        # approach where ctls dictate the flow
        # of the connection etc.

    async def listen(self, rpcroot: str) -> AsyncIterator[Optional[str]]:
        try:
            thiscon = self._ctls[rpcroot]
        except KeyError as ex:
            raise RuntimeError("ERROR: dir not announced") from ex

        rpcserver = RPCServer(rpcroot, thiscon.hostname, thiscon.port, thiscon.ssl)
        async for linedir in rpcserver.dolisten():
            yield linedir
