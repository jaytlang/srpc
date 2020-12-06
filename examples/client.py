import asyncio
import random
import json
import ssl

from srpc.nine.dat import AuthRequest, AttachRequest, ReqId, WalkRequest, \
    StatRequest, AppendRequest,RespId, ClunkRequest

from srpc.srv.msg import encode_message, decode_message, Message

def parse9(intxt: str) -> Message:
    splitinput = intxt.split()
    cmd = splitinput[0]
    if cmd == "auth":
        if len(splitinput) != 4:
            raise ValueError("command must have 4 parts")
        authafid = int(splitinput[1])
        authreq = AuthRequest(authafid, splitinput[2], splitinput[3])
        print(f"\t> {authreq}")
        authreq_bytes: bytes = json.dumps(authreq._asdict()).encode('utf-8')
        return Message(ReqId.AUTH.value, random.randrange(1, 5000), authreq_bytes)

    if cmd == "attach":
        if len(splitinput) != 5:
            raise ValueError("command must have 5 parts")
        attafid = int(splitinput[1])
        attfid = int(splitinput[2])

        attreq = AttachRequest(attafid, attfid, splitinput[3], splitinput[4])
        print(f"\t> {attreq}")
        attreq_bytes = json.dumps(attreq._asdict()).encode('utf-8')
        return Message(ReqId.ATTACH.value, random.randrange(1, 5000), attreq_bytes)

    if cmd == "walk":
        if len(splitinput) != 4:
            raise ValueError()
        walkfid = int(splitinput[1])
        walknfid = int(splitinput[2])

        walkreq = WalkRequest(walkfid, walknfid, splitinput[3])
        print(f"\t> {walkreq}")
        walkreq_bytes = json.dumps(walkreq._asdict()).encode('utf-8')
        return Message(ReqId.WALK.value, random.randrange(1, 5000), walkreq_bytes)

    if cmd == "stat":
        if len(splitinput) != 2:
            raise ValueError()
        statfid = int(splitinput[1])

        statreq = StatRequest(statfid)
        print(f"\t> {statreq}")
        statreq_bytes = json.dumps(statreq._asdict()).encode('utf-8')
        return Message(ReqId.STAT.value, random.randrange(1, 5000), statreq_bytes)

    if cmd == "append":
        if len(splitinput) != 3:
            raise ValueError()
        wrfid = int(splitinput[1])
        data = splitinput[2]

        writereq = AppendRequest(wrfid, data)
        print(f"\t> {writereq}")
        writereq_bytes = json.dumps(writereq._asdict()).encode('utf-8')
        return Message(ReqId.APPEND.value, random.randrange(1, 5000), writereq_bytes)

    if cmd == "clunk":
        if len(splitinput) != 2:
            raise ValueError()
        clfid = int(splitinput[1])

        clunkreq = ClunkRequest(clfid)
        print(f"\t> {clunkreq}")
        clunkreq_bytes = json.dumps(clunkreq._asdict()).encode('utf-8')
        return Message(ReqId.CLUNK.value, random.randrange(1, 5000), clunkreq_bytes)

    raise ValueError("Invalid command: " + cmd)

# This is just a test. Connect to some
# fixed server/port:
async def main() -> None:
    srv_address = "localhost"
    srv_port = 42069

    cert = "srpc.crt"

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_verify_locations(cert)
    context.verify_mode = ssl.CERT_REQUIRED

    print("Dialing server...")
    reader, writer = await asyncio.open_connection(
        srv_address,
        srv_port,
        ssl=context
    )

    print("Connected. The shell is yours.")

    while True:
        cmd = input("% ")
        try:
            msg = parse9(cmd)
        except ValueError as ex:
            print("Sorry, that's invalid. ", ex)
            continue
        writer.write(encode_message(msg))
        await writer.drain()
        rmsg : Message = await decode_message(reader)
        if rmsg.rpc != RespId.CLUNKR.value:
            data_json = json.loads(rmsg.data)
            assert isinstance(data_json, dict)
            print(f"\t< {data_json}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
