# Data structures for filesystem-to-server mapping.

# Through these, the server is able to flip 9P-like
# requests made through library routines into tangible
# operations on the host filesystem i.e. the UNIX
# sockets which the server is listening on at each
# endpoint. 

# FIDs and QIDs are just integers, so they don't
# require any introduction here. However, the
# translation of QID to filename does require
# such an introduction, beginning with how we
# represent file information...

# Right now there is one of these per connection.
# Eventually this is going to be one per user.
# For that reason, right now having a collision-prone
# FID space is fine because we fork ahead of every
# attachment, so these structures won't share
# any info
from typing import NamedTuple, Optional, Dict, List
import asyncio

class Stat(NamedTuple):
    qid: int
    fname: str  # Relative with respect to the fsroot
    isdir: bool
    children: List[str]

# Elements of the FID<->QID mapping
class FidData(NamedTuple):
    uname: str
    parentfid: Optional[int]
    qid: int

# Instead of having to syscall
# stat every time, cache the data
# in here which makes life marginally
# easier.
class QidData(NamedTuple):
    fname: str
    isdir: bool

ROOT_QID = 0

# Shared datastructures
FidTable: Dict[int, FidData] = {}
QidTable: Dict[int, QidData] = {}
