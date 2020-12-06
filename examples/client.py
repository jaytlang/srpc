import asyncio
import json

from srpc.nine.dat import AuthRequest, AttachRequest, MessageType, WalkRequest, \
    StatRequest, AppendRequest, ClunkRequest

from srpc.srv.dat import encode_message, decode_message, Message, SSLContextBuilder

class Client:
    def __init__(self) -> None:
        self._tag = 0

    def parse9(self, intxt: str) -> Message:
        splitinput = intxt.split()
        cmd = splitinput[0]
        if cmd == "auth":
            authafid = int(splitinput[1])
            uname = splitinput[2]
            aname = splitinput[3]
            authreq = AuthRequest(authafid, uname, aname)
            print(f"\t> {authreq}")
            authreq_bytes: bytes = json.dumps(authreq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.AUTH, tag, authreq_bytes)

        if cmd == "attach":
            attafid = int(splitinput[1])
            attfid = int(splitinput[2])
            uname = splitinput[3]
            aname = splitinput[4]
            attreq = AttachRequest(attafid, attfid, uname, aname)
            print(f"\t> {attreq}")
            attreq_bytes = json.dumps(attreq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.ATTACH, tag, attreq_bytes)

        if cmd == "walk":
            walkfid = int(splitinput[1])
            walknfid = int(splitinput[2])
            path = splitinput[3]
            walkreq = WalkRequest(walkfid, walknfid, path)
            print(f"\t> {walkreq}")
            walkreq_bytes = json.dumps(walkreq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.WALK, tag, walkreq_bytes)

        if cmd == "stat":
            statfid = int(splitinput[1])
            statreq = StatRequest(statfid)
            print(f"\t> {statreq}")
            statreq_bytes = json.dumps(statreq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.STAT, tag, statreq_bytes)

        if cmd == "append":
            wrfid = int(splitinput[1])
            data = splitinput[2]
            writereq = AppendRequest(wrfid, data)
            print(f"\t> {writereq}")
            writereq_bytes = json.dumps(writereq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.APPEND, tag, writereq_bytes)

        if cmd == "clunk":
            clfid = int(splitinput[1])
            clunkreq = ClunkRequest(clfid)
            print(f"\t> {clunkreq}")
            clunkreq_bytes = json.dumps(clunkreq._asdict()).encode('utf-8')
            tag = self._tag
            self._tag += 1
            return Message(MessageType.CLUNK, tag, clunkreq_bytes)

        raise ValueError("Invalid command: " + cmd)

# This is just a test. Connect to some
# fixed server/port:
async def main() -> None:
    srv_address = "localhost"
    srv_port = 42069

    cert = "srpc.crt"

    ssl_context_builder = SSLContextBuilder(cert)
    context = ssl_context_builder.build_client()

    print("Dialing server...")
    reader, writer = await asyncio.open_connection(
        srv_address,
        srv_port,
        ssl=context
    )

    print("Connected. The shell is yours.")
    client = Client()

    while True:
        cmd = input("% ")
        try:
            msg = client.parse9(cmd)
        except ValueError as ex:
            print("Sorry, that's invalid. ", ex)
            continue
        writer.write(encode_message(msg))
        await writer.drain()
        rmsg = await decode_message(reader)
        if rmsg.message_type != MessageType.CLUNKR:
            data_json = json.loads(rmsg.data)
            assert isinstance(data_json, dict)
            print(f"\t< {data_json}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
