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
from typing import NamedTuple

class ReqId(Enum):
    AUTH = 1        # AUTH tag (afid uname aname)
    ATTACH = 3      # ATTACH tag (afid fid uname aname)
    WALK = 5        # WALK tag (fid newfid path)
    STAT = 7        # STAT tag (fid)
    READ = 9        # READ tag (fid cnt)
    APPEND = 11     # APPEND tag (fid cnt data...)
    CLUNK = 13      # CLUNK tag (fid)

# RPC type on the receiver side:
class RespId(Enum):
    AUTHR = 2       # AUTHR tag (aqid)
    ATTACHR = 4     # ATTACHR tag (qid)
    WALKR = 6       # WALKR tag (qid)
    STATR = 8       # STATR tag (Stat)
    READR = 10      # READR tag (cnt data...)
    APPENDR = 12    # APPENDR tag (cnt)
    CLUNKR = 14     # CLUNKR tag
    ERROR = 99      # ERROR tag Error

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

class ReadRequest(NamedTuple):
    fid: int
    cnt: int

class ReadResponse(NamedTuple):
    cnt: int
    data: str

class AppendRequest(NamedTuple):
    fid: int
    cnt: int
    data: str

class AppendResponse(NamedTuple):
    cnt: int

class ClunkRequest(NamedTuple):
    fid: int

class ErrorResponse(NamedTuple):
    errno: int

