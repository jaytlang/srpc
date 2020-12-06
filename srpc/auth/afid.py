# Authentication file - related routines
# For now, this is a shim layer which doesn't
# actually implement fs-related primitives.
# Rather, it utilizes a thin 9P server
# layer to do the bare minimum for reads and
# writes, authenticating through PAM.

# It isn't the job of the afid to specify
# the authentication protocol, we leave that
# to auth modules also implemented here...

import pathlib

import pam

from srpc.auth.dat import AFidData, AFidTable, AFidValidity
from srpc.nine.dat import Error, RPCException

def sanitize_path(rpath: str) -> str:
    return str(pathlib.Path(rpath))

def authenticate(uname: str, passwd: str) -> bool:
    p = pam.pam()
    return p.authenticate(uname, passwd)

# Attach is obviously unsupported
# Walk is obviously unsupported
# Stat is obviously unsupported

# Good practice to dispose of your tokens
# Maybe there can be a timeout on these
def clunk_afid(fidno: int) -> None:
    try:
        del AFidTable[fidno]
        del AFidValidity[fidno]
    except KeyError:
        pass

# Auth itself
# Currently returns a dummy QID
# equal to the original FID
def mk_auth_afid(fidno: int, uname: str, aname: str) -> None:
    if fidno in AFidTable.keys():
        raise RPCException(Error.EREUSEFD)

    newdata = AFidData(uname, sanitize_path(aname))
    AFidTable[fidno] = newdata
    AFidValidity[fidno] = False

# These are all simple, synchronous operations...write included
def write_afid(fidno: int, data: str) -> str:
    if fidno not in AFidTable:
        raise RPCException(Error.ENOSCHFD)

    # For now, we're making this simple: the password
    # is written to the clientmsg side of the afid.
    # The server authenticates this against PAM.

    if authenticate(AFidTable[fidno].uname, data):
        AFidValidity[fidno] = True

    if AFidValidity[fidno]:
        return "1"
    return "0"
