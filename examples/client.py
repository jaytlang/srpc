import asyncio
import random
import json
import ssl
from typing import List
from getpass import getpass
from srpc.lib.llapi import *

def parse9(intxt: str) -> Message:
    splitinput : List[str] = intxt.split()
    cmd : str = splitinput[0]
    if cmd == "auth":
        if(len(splitinput) != 4): raise ValueError
        try: authafid : int = int(splitinput[1])
        except: raise ValueError
        
        authreq = AuthRequest(authafid, splitinput[2], splitinput[3])
        print(f"\t> {authreq}")
        authreq_bytes : bytes = json.dumps(authreq._asdict()).encode('utf-8')
        return Message(ReqId.AUTH.value, random.randrange(1, 5000), authreq_bytes)


    elif cmd == "attach":
        if(len(splitinput) != 5): raise ValueError
        try:
            attafid : int = int(splitinput[1])
            attfid : int = int(splitinput[2])
        except: raise ValueError

        attreq = AttachRequest(attafid, attfid, splitinput[3], splitinput[4])
        print(f"\t> {attreq}")
        attreq_bytes : bytes = json.dumps(attreq._asdict()).encode('utf-8')
        return Message(ReqId.ATTACH.value, random.randrange(1, 5000), attreq_bytes)

    elif cmd == "walk":
        if(len(splitinput) != 4): raise ValueError
        try:
            walkfid : int = int(splitinput[1])
            walknfid : int = int(splitinput[2])
        except: raise ValueError

        walkreq = WalkRequest(walkfid, walknfid, splitinput[3])
        print(f"\t> {walkreq}")
        walkreq_bytes : bytes = json.dumps(walkreq._asdict()).encode('utf-8')
        return Message(ReqId.WALK.value, random.randrange(1, 5000), walkreq_bytes)

    elif cmd == "stat":
        if(len(splitinput) != 2): raise ValueError
        try: statfid : int = int(splitinput[1])
        except: raise ValueError

        statreq = StatRequest(statfid)
        print(f"\t> {statreq}")
        statreq_bytes : bytes = json.dumps(statreq._asdict()).encode('utf-8')
        return Message(ReqId.STAT.value, random.randrange(1, 5000), statreq_bytes)

    elif cmd == "append":
        if(len(splitinput) != 3): raise ValueError
        try:
            wrfid : int = int(splitinput[1])
            data : str = splitinput[2]
        except: raise ValueError

        writereq = AppendRequest(wrfid, data)
        print(f"\t> {writereq}")
        writereq_bytes : bytes = json.dumps(writereq._asdict()).encode('utf-8')
        return Message(ReqId.APPEND.value, random.randrange(1, 5000), writereq_bytes)

    elif cmd == "clunk":
        if(len(splitinput) != 2): raise ValueError
        try: clfid : int = int(splitinput[1])
        except: raise ValueError

        clunkreq = ClunkRequest(clfid)
        print(f"\t> {clunkreq}")
        clunkreq_bytes : bytes = json.dumps(clunkreq._asdict()).encode('utf-8')
        return Message(ReqId.CLUNK.value, random.randrange(1, 5000), clunkreq_bytes)

    else: raise ValueError

# This is just a test. Connect to some
# fixed server/port:
async def main() -> None:
    srv_address = "localhost"
    srv_port = 42069
    
    ## End edits ##
    cert : str = "srpc.crt"
    key : str = "srpc.key"
    
    context : ssl.SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_verify_locations(cert)
    context.verify_mode = ssl.CERT_REQUIRED
    
    print("Dialing server...")
    reader : asyncio.StreamReader
    writer : asyncio.StreamWriter
    reader, writer = await asyncio.open_connection(
            srv_address,
            srv_port,
            ssl=context
            )
    
    print("Connected. The shell is yours.")
    
    while True:
        cmd = input("% ")
        try: msg : Message = parse9(cmd)
        except:
            print("Sorry, that's invalid.")
            continue
        writer.write(encode_message(msg))
        await writer.drain()
        rmsg : Message = await decode_message(reader)
        if rmsg.rpc != RespId.CLUNKR.value:
            data_json = json.loads(rmsg.data)
            assert isinstance(data_json, dict)
            print(f"\t< {data_json}")
    
    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
