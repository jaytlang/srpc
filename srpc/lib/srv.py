# High level server API

from typing import Dict
import os
import ssl
from srpc.srv.srv import RPCServer
from srpc.srv.dat import Con, Message, SSLContextBuilder

context : ssl.SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ctls : Dict[str, Con] = {}

# Configure the ssl context automatically, for ease of use
async def ssl_context_helper(certfile: str, keyfile: str) -> int:
    global context
    context.load_cert_chain(certfile = certfile, keyfile = keyfile)
    return 0

async def announce(hostname: str, port: int, rpcroot: str) -> str:
    global ctls
    global context

    newcon : Con = Con(hostname, port, context)
    if rpcroot in ctls.keys(): return "ERROR: dir already announced"
    ctls[rpcroot] = newcon
    
    # Make necessary control structures
    try: os.mkdir("/srv")
    except FileExistsError: pass
    
    try: os.mkdir("/srv/ctl/")
    except FileExistsError: pass

    # All good. ctl/ gets populated when
    # new connections pop open - for now,
    # per unix user for simplicity. This is
    # an effective simplifying assumption,
    # but one that deviates from the 9P
    # approach where ctls dictate the flow
    # of the connection etc.
    return rpcroot

async def listen(rpcroot: str) -> str:
    global ctls

    try: thiscon : Con = ctls[rpcroot]
    except KeyError: return "ERROR: dir not announced"

    rpcserver = RPCServer(rpcroot, thiscon.hostname, thiscon.port, thiscon.ssl) 
    return await rpcserver.dolisten(rpcroot)
