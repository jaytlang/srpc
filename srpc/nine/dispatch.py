# 9P handlers for each type of
# request. Marshal routines from
# the auth and fs layers, and tell
# the master server process when
# it should fork etc.

import json
import shutil
from typing import Set, NamedTuple
from srpc.fs.dat import Stat
from srpc.fs.fid import *
from srpc.fs.qid import clone
from srpc.auth.afid import *
from srpc.nine.dat import *
from srpc.auth.privs import validate_token, did_drop_privs, drop_privileges
from srpc.srv.dat import Message

async def dispatch9(msg: Message, rpcroot: str) -> Message:
    # Check if the RPC is a valid one  
    valid_requests : Set[int] = set(i.value for i in ReqId)
    if msg.rpc not in valid_requests: return encode_error(msg, Error.EFAKERPC.value)

    # If it is, decode the message
    data_json = json.loads(msg.data)
    assert isinstance(data_json, dict)
    
    # Switch off between message types
    if(msg.rpc == ReqId.AUTH.value):
        print("9: auth")
        # You are allowed to derive multiple authentication
        # tokens, but if this process has already dropped privs
        # to a given user this request presently fails. 
        if did_drop_privs(): return encode_error(msg, Error.EUNIMPLM.value)
        authreq9 = AuthRequest(**data_json)
        aqid : int = mk_auth_afid(authreq9.afid, authreq9.uname, authreq9.aname)
        if aqid < 0: return encode_error(msg, aqid)
        
        # So we haven't dropped privs and have a new afid. Good,
        # return this to the user for reading and writing.
        authresp : str = json.dumps(AuthResponse(aqid)._asdict())
        authresp_bytes: bytes = authresp.encode('utf-8')
        return Message(RespId.AUTHR.value, msg.tag, authresp_bytes)

    elif(msg.rpc == ReqId.ATTACH.value):
        print("9: attach")
        attreq9 = AttachRequest(**data_json)
        if did_drop_privs(): return encode_error(msg, Error.EUNIMPLM.value)

        # Before anything, check to make sure that the user is allowed
        # to make the insertion they are making.
        cloneroot : str = clone(rpcroot + "/" + attreq9.aname, attreq9.uname)
        print("Made clone dir") 
        attqid : int = mk_attach_fid(attreq9.fid, attreq9.uname, cloneroot + "/" + attreq9.aname)
        if attqid < 0:
            shutil.rmtree(cloneroot)
            return encode_error(msg, attqid)

        print("Made attach fid")

        # The qid is blindly set up. We will now need to clunk
        # it if authentication fails.
        # Actually do authentication
        if not validate_token(attreq9.afid, attreq9.uname, attreq9.aname):
            shutil.rmtree(cloneroot)
            clunk_fid(attreq9.fid)
            return encode_error(msg, Error.EAUTHENT.value)
        print("Tok validated")

        # If we've gotten this far the user is who they say they are.
        drop_privileges(attreq9.uname)

        # Otherwise, we are all sandboxed! Made a new fid for the
        # user as they request, so return it their way.
        attresp : str = json.dumps(AttachResponse(attqid)._asdict())
        attresp_bytes: bytes = attresp.encode('utf-8')
        return Message(RespId.ATTACHR.value, msg.tag, attresp_bytes)

    # From here on out, security is a non-issue
    # because of the way fids work. If we're worried
    # about modern brute forces, just make the fids longer
    elif(msg.rpc == ReqId.WALK.value):
        print("9: walk")
        walkreq9 = WalkRequest(**data_json)  
        walkqid : int = mk_walk_fid(walkreq9.newfid, walkreq9.fid, walkreq9.path)
        if walkqid < 0: return encode_error(msg, walkqid)

        walkresp : str = json.dumps(WalkResponse(walkqid)._asdict())
        walkresp_bytes: bytes = walkresp.encode('utf-8')
        return Message(RespId.WALKR.value, msg.tag, walkresp_bytes)

    elif(msg.rpc == ReqId.STAT.value):
        print("9: stat")
        statreq9 = StatRequest(**data_json)
        stat : Stat = stat_fid(statreq9.fid)
        if stat.qid < 0: return encode_error(msg, stat.qid)

        statresp : str = json.dumps(StatResponse(stat.qid, stat.fname, stat.isdir)._asdict())
        statresp_bytes: bytes = statresp.encode('utf-8')
        return Message(RespId.STATR.value, msg.tag, statresp_bytes)

    elif(msg.rpc == ReqId.READ.value):
        print("9: read")
        readreq9 = ReadRequest(**data_json)

        data : str
        status : int
        data, status = await read_fid(readreq9.fid, readreq9.cnt)
        if status < 0: return encode_error(msg, status)

        readresp : str = json.dumps(ReadResponse(len(data), data)._asdict())
        readresp_bytes: bytes = readresp.encode('utf-8')
        return Message(RespId.READR.value, msg.tag, readresp_bytes)

    elif(msg.rpc == ReqId.APPEND.value):
        print("9: write")
        wrreq9 = AppendRequest(**data_json)
        count : int = await write_fid(wrreq9.fid, wrreq9.cnt, wrreq9.data)

        wrresp : str = json.dumps(AppendResponse(count)._asdict())
        wrresp_bytes : bytes = wrresp.encode('utf-8')
        return Message(RespId.APPENDR.value, msg.tag, wrresp_bytes)

    else:
        print("9: clunk")
        clunkreq9 = ClunkRequest(**data_json)
        clunk_fid(clunkreq9.fid)
        clunkresp_bytes : bytes = "".encode('utf-8')
        return Message(RespId.CLUNKR.value, msg.tag, clunkresp_bytes)
        
def encode_error(original_msg: Message, errno: int) -> Message:
    print("9: error code %d", errno)
    err_resp : str = json.dumps(ErrorResponse(errno)._asdict())
    err_bytes : bytes = err_resp.encode('utf-8')
    return Message(RespId.ERROR.value, original_msg.tag, err_bytes)

