# FID<->QID mapping logic

import pathlib
from typing import Tuple, Dict
from srpc.fs.dat import FidData, QidTable, Stat
from srpc.fs.qid import qid_for_aname, stat_qid, write_qid
from srpc.auth.afid import write_afid, clunk_afid
from srpc.nine.dat import Error

def sanitize_path(rpath: str) -> str:
    return str(pathlib.Path(rpath))

def parent_path(rpath: str) -> str:
    return str(pathlib.Path(rpath).parent)

# Given a (prevalidated) user, inject a new entry into the
# FID table with no parent and the passed attributes.
# Returns the QID associated with this new FID.
def mk_attach_fid(fidno: int, uname: str, aname: str, fidtable: Dict[int, FidData]) -> int:
    aname_qid: int = qid_for_aname(sanitize_path(aname))
    if aname_qid < 0: return aname_qid

    if fidno in fidtable.keys(): return Error.EREUSEFD.value

    newdata: FidData = FidData(uname, None, aname_qid)
    fidtable[fidno] = newdata
    return aname_qid

def mk_walk_fid(fidno: int, parentfid: int, relpath: str, fidtable: Dict[int, FidData]) -> int:
    try:
        olddata: FidData = fidtable[parentfid]
    except KeyError: return Error.ENOSCHFD.value

    if fidno in fidtable.keys(): return Error.EREUSEFD.value
    
    newpath: str = QidTable[olddata.qid].fname
    if ".." in relpath: newpath = parent_path(newpath)
    else: newpath = sanitize_path(newpath + "/" + relpath)

    newpath_qid: int = qid_for_aname(newpath)
    if newpath_qid < 0: return newpath_qid
    
    newdata: FidData = FidData(olddata.uname, parentfid, newpath_qid)
    fidtable[fidno] = newdata
    return newpath_qid

def stat_fid(fidno: int, fidtable: Dict[int, FidData]) -> Stat:
    try: 
        qid: int = fidtable[fidno].qid
    except KeyError: return Stat(Error.ENOSCHFD.value, "dontcare", False, [])
    return stat_qid(qid)

async def write_fid(fidno: int, count: int, data: str, fidtable: Dict[int, FidData]) -> Tuple[str, int]:
    try: 
        qid: int = fidtable[fidno].qid
    except KeyError: 
        # Try the AFID table as well
        return write_afid(fidno, count, data)

    actualcount: int = len(data)
    if(count < actualcount):
        actualcount = count
        data = data[0:count - 1]
    
    return await write_qid(fidtable[fidno].qid, data)

def clunk_fid(fidno: int, fidtable: Dict[int, FidData]) -> None:
    try: del fidtable[fidno]
    except KeyError: pass
    clunk_afid(fidno)
