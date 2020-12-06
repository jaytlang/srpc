# 9P handlers for each type of
# request. Marshal routines from
# the auth and fs layers, and tell
# the master server process when
# it should fork etc.

import json
import shutil
import asyncio
import pwd
import grp
import os
import multiprocessing
from typing import Dict

from srpc.fs.fid import Error, clunk_fid, FidData, mk_attach_fid, mk_walk_fid, write_fid, stat_fid
from srpc.fs.qid import Qid
from srpc.auth.afid import mk_auth_afid
from srpc.auth.dat import Relays
from srpc.auth.privs import validate_token
from srpc.nine.dat import MessageType, AuthRequest, AuthResponse, AttachRequest, \
    AttachResponse, WalkRequest, WalkResponse, AppendRequest, AppendResponse, \
    ErrorResponse, ClunkRequest, ClunkResponse, StatRequest, StatResponse
from srpc.srv.dat import Message, encode_message, decode_message

async def dispatch9(
    msg: Message,
    rpcroot: str,
    fidtable: Dict[int, FidData],
    qid: Qid,
    contained: bool
) -> Message:
    data_json = json.loads(msg.data)
    assert isinstance(data_json, dict)

    # Switch off between message types
    if msg.message_type == MessageType.AUTH:
        if contained:
            raise ValueError()

        print("9: auth")
        # You are allowed to derive multiple authentication
        # tokens, but if this process has already dropped privs
        # to a given user this request presently fails.
        authreq9 = AuthRequest(**data_json)
        aqid = mk_auth_afid(authreq9.afid, authreq9.uname, authreq9.aname)
        if aqid < 0:
            return encode_error(msg, aqid)

        # So we haven't dropped privs and have a new afid. Good,
        # return this to the user for reading and writing.
        authresp = json.dumps(AuthResponse(aqid)._asdict())
        authresp_bytes = authresp.encode('utf-8')
        return Message(MessageType.AUTHR, msg.tag, authresp_bytes)

    if msg.message_type == MessageType.ATTACH:
        if contained:
            raise ValueError()

        print("9: attach")
        attreq9 = AttachRequest(**data_json)

        # Before anything, check to make sure that the user is allowed
        # to make the insertion they are making.
        cloneroot = qid.clone(rpcroot + "/" + attreq9.aname)
        print("Made clone dir")
        attqid = mk_attach_fid(
            attreq9.fid, attreq9.uname,
            cloneroot + "/" + attreq9.aname,
            fidtable,
            qid
        )
        if attqid < 0:
            shutil.rmtree(cloneroot)
            return encode_error(msg, attqid)

        print("Made attach fid")

        # The qid is blindly set up. We will now need to clunk
        # it if authentication fails.
        # Actually do authentication
        if not validate_token(attreq9.afid, attreq9.uname, attreq9.aname):
            shutil.rmtree(cloneroot)
            clunk_fid(attreq9.fid, fidtable)
            return encode_error(msg, Error.EAUTHENT)
        print("Tok validated")

        # If we've gotten this far the user is who they say they are.
        drop_privileges(attreq9.uname, fidtable, rpcroot)

        # Otherwise, we are all sandboxed! Made a new fid for the
        # user as they request, so return it their way.
        attresp : str = json.dumps(AttachResponse(attqid)._asdict())
        attresp_bytes: bytes = attresp.encode('utf-8')
        return Message(MessageType.ATTACHR, msg.tag, attresp_bytes)

    # From here on out, security is a non-issue
    # because of the way fids work. If we're worried
    # about modern brute forces, just make the fids longer
    if msg.message_type == MessageType.WALK:
        walkreq9 = WalkRequest(**data_json)

        if contained or walkreq9.fid not in fidtable.keys():
            print("9: walk")
            walkqid : int = mk_walk_fid(walkreq9.newfid, walkreq9.fid, walkreq9.path, fidtable, qid)
            if walkqid < 0:
                return encode_error(msg, walkqid)

            walkresp = json.dumps(WalkResponse(walkqid)._asdict())
            walkresp_bytes: bytes = walkresp.encode('utf-8')
            return Message(MessageType.WALKR, msg.tag, walkresp_bytes)
        walkuname = fidtable[walkreq9.fid].uname
        return await proxy9(walkuname, msg)

    if msg.message_type == MessageType.STAT:
        statreq9 = StatRequest(**data_json)

        if contained or statreq9.fid not in fidtable.keys():
            print("9: stat")
            stat = stat_fid(statreq9.fid, fidtable, qid)
            if stat.qid < 0:
                return encode_error(msg, stat.qid)

            stat_resp = StatResponse(stat.qid, stat.fname, stat.isdir, stat.children)
            statresp_bytes = json.dumps(stat_resp._asdict()).encode('utf-8')
            return Message(MessageType.STATR, msg.tag, statresp_bytes)
        uname = fidtable[statreq9.fid].uname
        return await proxy9(uname, msg)

    if msg.message_type == MessageType.APPEND:
        apreq9 = AppendRequest(**data_json)

        if contained or apreq9.fid not in fidtable.keys():
            print("9: append")
            data = await write_fid(apreq9.fid, apreq9.data, fidtable, qid)
            if data[1] < 0:
                return encode_error(msg, data[1])

            wrresp = json.dumps(AppendResponse(data[0])._asdict())
            wrresp_bytes = wrresp.encode('utf-8')
            return Message(MessageType.APPENDR, msg.tag, wrresp_bytes)
        appuname = fidtable[apreq9.fid].uname
        return await proxy9(appuname, msg)

    if msg.message_type == MessageType.CLUNK:
        # Run this boi unconfined, since it never touches the qid layer
        # and it just deals with fids
        print("9: clunk")
        clunkreq9 = ClunkRequest(**data_json)
        clunk_fid(clunkreq9.fid, fidtable)
        clunkresp_bytes = json.dumps(ClunkResponse()._asdict()).encode('utf8')
        return Message(MessageType.CLUNKR, msg.tag, clunkresp_bytes)

    raise RuntimeError("invalid message type")

async def proxy9(uname: str, message: Message) -> Message:
    print("9: proxy")
    ctl = "/srv/ctl/" + str(Relays[uname])

    reader, writer = await asyncio.open_unix_connection(ctl)
    writer.write(encode_message(message))
    await writer.drain()

    rmessage = await decode_message(reader)
    writer.close()
    await writer.wait_closed()
    return rmessage

def encode_error(original_msg: Message, errno: Error) -> Message:
    print("9: error code %d", errno)
    err_resp = json.dumps(ErrorResponse(errno.value)._asdict())
    err_bytes = err_resp.encode('utf-8')
    return Message(MessageType.ERROR, original_msg.tag, err_bytes)

# 9AUTH: PRIVILEGE DROPPING LOGIC #
# Have we descended to an unprivileged user yet?
ctlcount : int = 1

# Actually perform the descent
def drop_privileges(uname: str, fidtable: Dict[int, FidData], rpcroot: str) -> None:
    global ctlcount

    # We are about to descend to the new user through a fork
    # operation. Once forked, permissions will get lowered
    # and the child will initiate a server to catch further
    # stuff from us.

    if uname in Relays.keys():
        return
    Relays[uname] = ctlcount
    ctlcount += 1

    child = multiprocessing.Process(target=mpenter, args=(Relays[uname], uname, rpcroot, fidtable))
    child.start()

    print(f"9auth: successfully dropped privs on attach, root -> {uname}")

# MULTIUSER SHIM LAYER #
myfidtable: Dict[int, FidData] = {}
myrpcroot = ""
myctl = 0
myqid = Qid()

# On initialization, receives a reference
# to the master fid dictionary for this connection,
# in addition to the user to downgrade to and
# the ctl to utilize.
def mpenter(ctl: int, uname: str, rpcroot: str, fidtable: Dict[int, FidData], qid: Qid) -> None:
    global myfidtable
    global myrpcroot
    global myctl
    global myqid

    # First, drop privileges and store proc-specific vars
    newuid : int = pwd.getpwnam(uname)[2]
    newgid : int = grp.getgrnam(uname)[2]
    os.setgid(newgid)
    os.setuid(newuid)

    myfidtable = fidtable
    myrpcroot = rpcroot
    myctl = ctl
    myqid = qid

    asyncio.run(start9fs())

# Asynchronous entry point. Start up a server
async def start9fs() -> None:
    global myctl

    server = await asyncio.start_unix_server(
        fs9,
        f"/srv/ctl/{myctl}"
    )

    await server.serve_forever()

    print("9: ctl file started with reduced permissions")

# One time confined fs access
async def fs9(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    global myfidtable
    global myrpcroot
    global myctl
    global myqid

    try:
        request = await decode_message(reader)
    except asyncio.IncompleteReadError:
        writer.close()
        await writer.wait_closed()
        return None

    response = await dispatch9(request, myrpcroot, myfidtable, myqid, True)
    writer.write(encode_message(response))
    await writer.drain()
    writer.close()
