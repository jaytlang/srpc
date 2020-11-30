# Validation and privilege management, first pass.

from srpc.auth.dat import *
import pathlib
import pwd
import grp
import os

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

# Have we descended to an unprivileged user yet?
def did_drop_privs() -> bool: return dropped

# Set our UID/GID to a different user, thus picking
# up SELinux policy associated with that user.
# dropped MUST be false in order to run this.
def drop_privileges(uname: str) -> None:
    global dropped

    newuid : int = pwd.getpwnam(uname)[2]
    newgid : int = grp.getgrnam(uname)[2]
    os.setgid(newgid)
    os.setuid(newuid)

    # We are the new user now - set some things up
    dropped = True
    print(f"9auth: successfully dropped privs on attach, root -> {uname}")


