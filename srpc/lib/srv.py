# High level server API

from typing import Dict
import os
import ssl
from srpc.srv.srv import RPCServer
from srpc.srv.dat import Con, Message, SSLContextBuilder

context : ssl.SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ctls : Dict[str, Con] = {}
ctlcount : int = 0

# Configure the ssl context automatically, for ease of use
async def ssl_context_helper(certfile: str, keyfile: str) -> int:
    global context
    context.load_cert_chain(certfile = certfile, keyfile = keyfile)
    return 0

async def announce(hostname: str, port: int, rpcroot: str) -> str:
    global ctls
    global ctlcount
    global context

    newcon : Con = Con(hostname, port, ctlcount, context)
    if rpcroot in ctls.keys(): return "ERROR: dir already announced"
    ctls[rpcroot] = newcon
    ctlcount += 1
    
    # Make necessary control structures
    try: os.mkdir("/srv")
    except FileExistsError: pass
    
    try: os.mkdir("/srv/ctl/")
    except FileExistsError: pass
    
    ctlpath: str = f"/srv/ctl/{ctlcount - 1}"
    try: os.mkdir(ctlpath)
    except FileExistsError: pass
    
    try: os.unlink(ctlpath + "/send")
    except FileNotFoundError: pass
    try: os.unlink(ctlpath + "/recv")
    except FileNotFoundError: pass
    
    os.mkfifo(ctlpath + "/send")
    os.mkfifo(ctlpath + "/recv")
    return ctlpath

async def listen(rpcroot: str) -> str:
    global ctls
    global ctlcount
    global context

    try: thiscon : Con = ctls[rpcroot]
    except KeyError: return "ERROR: dir not announced"

    rpcserver = RPCServer(rpcroot, thiscon.hostname, thiscon.port, thiscon.ssl) 
    return await rpcserver.dolisten(rpcroot)
