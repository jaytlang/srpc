# Validation and privilege management, first pass.

from srpc.auth.dat import *
import pathlib

dropped : bool = False

def sanitize_path(rpath: str) -> str:
    return str(pathlib.Path(rpath))

# Is an afid valid?
def validate_token(afid: int, uname: str, aname: str) -> bool:
    if afid not in AFidTable.keys(): return False
    print("Auth: afid exists")
    if not AFidValidity[afid]: return False
    print("Auth: afid is valid")
    if uname != AFidTable[afid].uname: return False
    print("Auth: uname works out")
    print("Auth: path: ", sanitize_path(aname))
    if sanitize_path(aname) != AFidTable[afid].aname: return False
    print("Auth: path works out")

    return True

