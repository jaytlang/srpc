# Remote file control primitives / data structures

# RPC types correspond to the following.
# This is a subset of 9P, except it
# does not delegate authentication (for now),
# instead assuming a secure connection,
# and leaves open/close implicit to read/write.
#
# AUTH:  instantiate a connection, where fid is taken
#        as the root of the RPC tree and aname is the
#        client's selection of the root, should they
#        only desire a subset of the RPC tree
#
# WALK:  register a new fid which corresponds to the
#        passed path, i.e. descend the directory tree
#
# STAT:  get a Stat struct which contains information
#        about a fid, chiefly names and possibly
#        other metadata
#
# READ:  read a file pointed to by fid. If it's a directory
#        return a list of names of files in the directory
#        or a list of stat structures in json form. This
#        is used to get return values from RPCs.
#
# APPEND:write to a file, i.e. call an RPC.
#
# CLUNK: Unmap a fid/qid mapping, allowing the client to
#        reuse it for a different server file / qid.

# I'm using some 9P parlance here...fid refers
# to a unique identifier chosen by the client
# to refer to a file. New fids are only generated
# through AUTH and WALK calls, enabling optional
# implicit session identification by tracing
# the ancestry of a given fid.
#
# qid refers to a unique identifier utilized
# by the server for each file. Every server
# RPC socket/template file must have a unique
# qid, while multiple fids may (and may have to)
# point to a given qid.

from enum import Enum
from typing import NamedTuple, List

class MessageType(Enum):
    ERROR = -1      # ERROR tag Error
    AUTH = 1        # AUTH tag (afid uname aname)
    AUTHR = 2       # AUTHR tag (aqid)
    ATTACH = 3      # ATTACH tag (afid fid uname aname)
    ATTACHR = 4     # ATTACHR tag (qid)
    WALK = 5        # WALK tag (fid newfid path)
    WALKR = 6       # WALKR tag (qid)
    STAT = 7        # STAT tag (fid)
    STATR = 8       # STATR tag (Stat)
    APPEND = 9      # APPEND tag (fid data...)
    APPENDR = 10    # APPENDR tag (data...)
    CLUNK = 11      # CLUNK tag (fid)
    CLUNKR = 12     # CLUNKR tag

# Error messages -- work in progress
class Error(Enum):
    EAUTHENT = -1
    EFAKERPC = -2
    EBADPATH = -3
    EOPENWRF = -4
    EOPENRDF = -5
    ENOSCHFD = -6
    EREUSEFD = -7
    EILLEGAL = -8
    EUNIMPLM = -9
    EFESCAPE = -10

# More classes for these types. These can
# be json'ified and encoded generically, and
# then stapled into Messages with the type and
# tag field like you currently do it.

class AuthRequest(NamedTuple):
    afid: int
    uname: str
    aname: str

class AuthResponse(NamedTuple):
    aqid: int

class AttachRequest(NamedTuple):
    afid: int
    fid: int
    uname: str
    aname: str

class AttachResponse(NamedTuple):
    qid: int

class WalkRequest(NamedTuple):
    fid: int
    newfid: int
    path: str

class WalkResponse(NamedTuple):
    qid: int

class StatRequest(NamedTuple):
    fid: int

class StatResponse(NamedTuple):
    qid: int
    fname: str
    isdir: bool
    children: List[str]

class AppendRequest(NamedTuple):
    fid: int
    data: str

class AppendResponse(NamedTuple):
    data: str

class ClunkRequest(NamedTuple):
    fid: int

class ClunkResponse(NamedTuple):
    pass

class ErrorResponse(NamedTuple):
    errno: int

class RPCException(Exception):
    def __init__(self, errno: int):
        self.errno = Error(errno)
        super().__init__()
