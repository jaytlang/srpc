# FID<->QID mapping logic

import pathlib
from typing import Dict
from srpc.fs.dat import FidData, Stat
from srpc.fs.qid import Qid
from srpc.auth.afid import write_afid, clunk_afid
from srpc.nine.dat import Error, RPCException

def sanitize_path(rpath: str) -> str:
    return str(pathlib.Path(rpath))

def parent_path(rpath: str) -> str:
    return str(pathlib.Path(rpath).parent)

# Given a (prevalidated) user, inject a new entry into the
# FID table with no parent and the passed attributes.
# Returns the QID associated with this new FID.
def mk_attach_fid(
    fidno: int,
    uname: str,
    aname: str,
    fidtable: Dict[int, FidData],
    qid: Qid
) -> int:
    aname_qid = qid.qid_for_aname(sanitize_path(aname))

    if fidno in fidtable.keys():
        raise RPCException(Error.EREUSEFD)

    newdata = FidData(uname, None, aname_qid)
    fidtable[fidno] = newdata
    return aname_qid

def mk_walk_fid(
    fidno: int,
    parentfid: int,
    relpath: str,
    fidtable: Dict[int, FidData],
    qid: Qid
) -> int:
    try:
        olddata = fidtable[parentfid]
    except KeyError as ex:
        raise RPCException(Error.ENOSCHFD) from ex

    if fidno in fidtable.keys():
        raise RPCException(Error.EREUSEFD)

    newpath = qid.qid_table[olddata.qid].fname
    if ".." in relpath:
        newpath = parent_path(newpath)
    else:
        newpath = sanitize_path(newpath + "/" + relpath)

    newpath_qid = qid.qid_for_aname(newpath)

    newdata = FidData(olddata.uname, parentfid, newpath_qid)
    fidtable[fidno] = newdata
    return newpath_qid

def stat_fid(fidno: int, fidtable: Dict[int, FidData], qid: Qid) -> Stat:
    try:
        qid_num = fidtable[fidno].qid
    except KeyError as ex:
        raise RPCException(Error.ENOSCHFD) from ex
    return qid.stat_qid(qid_num)

async def write_fid(
    fidno: int,
    data: str,
    fidtable: Dict[int, FidData],
    qid: Qid
) -> str:
    if fidno not in fidtable:
        return write_afid(fidno, data)

    return await qid.write_qid(fidtable[fidno].qid, data)

def clunk_fid(fidno: int, fidtable: Dict[int, FidData]) -> None:
    try:
        del fidtable[fidno]
    except KeyError:
        pass
    clunk_afid(fidno)
