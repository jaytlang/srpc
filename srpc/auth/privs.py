# Validation and privilege management, first pass.

import pathlib

from srpc.auth.dat import AFidTable, AFidValidity
from srpc.nine.dat import Error, RPCException

dropped: bool = False

def sanitize_path(rpath: str) -> str:
    return str(pathlib.Path(rpath))

# Is an afid valid?
def validate_token(afid: int, uname: str, aname: str) -> None:
    if afid not in AFidTable.keys():
        raise RPCException(Error.EAUTHENT)
    print("Auth: afid exists")
    if not AFidValidity[afid]:
        raise RPCException(Error.EAUTHENT)
    print("Auth: afid is valid")
    if uname != AFidTable[afid].uname:
        raise RPCException(Error.EAUTHENT)
    print("Auth: uname works out")
    print("Auth: path: ", sanitize_path(aname))
    if sanitize_path(aname) != AFidTable[afid].aname:
        raise RPCException(Error.EAUTHENT)
    print("Auth: path works out")
