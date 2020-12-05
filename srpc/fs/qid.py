# QID<->System logic
# Manage the mapping between QIDs
# and socket files.

import asyncio
import shutil
import os
import pwd
import grp
from typing import Tuple, List
from srpc.fs.dat import QidData, QidTable, Stat, ROOT_QID
from srpc.fs.unix import write_pipe, read_pipe
from srpc.nine.dat import Error

# qidcount 0 is reserved for the root at the moment
# work around this by setting the initial count to 1
qidcount: int = 1
concount: int = 1

# Initialization: clone the template filesystem
# into a new tree of named pipes for a given user
def clone(fsroot: str, uname: str) -> str:
    global concount
    # Recurse through the filesystem on disk and
    # copy sockets into a tree. By default, this
    # winds up a directory above the fsroot in 
    # a directory numbered by concount, as such...
    cloneroot: str = f"/srv/{concount}/"
    while(os.path.isdir(cloneroot)):
        concount += 1
        cloneroot = f"/srv/{concount}/"

    def all_templates(fsroot: str) -> List[str]:
        fpaths: List[str] = []
        for root, dirs, files in os.walk(fsroot):
            for d in dirs: fpaths.append(os.path.join(root, d))
            for f in files: fpaths.append(os.path.join(root, f))
    
        return fpaths

    # For every file in the directory here,
    # instantiate two named pipes with
    # the same name as that file, one for sending
    # and one for receiving.
    os.mkdir(cloneroot)
    for fpath in all_templates(fsroot):
        clonepath: str = fpath.replace(fsroot, cloneroot)
        # If we've got a directory
        # - mkdir
        # - register
        # - copystat
        # - chown
        if os.path.isdir(fpath):
            os.mkdir(clonepath)
            register_qid(clonepath, True)
            shutil.copystat(fpath, clonepath)
            shutil.chown(
                    clonepath,
                    user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                    group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                    )

            print("Registered directory", clonepath)

        # If we've got a file, make a send/recv pair
        # - mkdir
        # - mkfifo x 2
        # - copystat x 2
        # - chmod x 1 -- need to create a generic directory
        # - chown x 3
        else:
            os.mkdir(clonepath)
            os.chmod(clonepath, 0o755)
            shutil.chown(
                    clonepath,
                    user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                    group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                    )
            register_qid(clonepath, False)
            print("Registered pre-file", clonepath)

            os.mkfifo(clonepath + "/recv")
            os.mkfifo(clonepath + "/send")

            shutil.chown(
                    clonepath + "/recv",
                    user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                    group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                    )
            
            shutil.chown(
                    clonepath + "/send",
                    user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                    group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                    )

    # Manually register the root directory
    # since os.walk won't cover it
    # The context of this dir doesn't matter.
    register_qid(cloneroot[:-1], True, isroot = True)
    print("Registered", cloneroot[:-1])

    return cloneroot

def qid_for_aname(fname: str) -> int:
    print("Checking", fname)
    for qid in QidTable.keys():
        if QidTable[qid].fname == fname: return qid

    return Error.EBADPATH.value

def register_qid(path: str, isdir: bool, isroot: bool = False) -> None:
    global qidcount
    # Pop the QID into the table, with
    # no associated writer/reader for the
    # time being.
    if not isroot:
        QidTable[qidcount] = QidData(path, isdir)
        qidcount += 1
    else: QidTable[0] = QidData(path, isdir)
    
def stat_qid(qid: int) -> Stat:
    data: QidData = QidTable[qid]

    # Strip off the fsroot
    fsroot: QidData = QidTable[ROOT_QID]
    userpath: str = data.fname.replace(fsroot.fname, "/")

    children: List[str] = []
    if data.isdir: children = [f for f in os.listdir(data.fname)]

    return Stat(qid, userpath, data.isdir, children) 

async def write_qid(qid: int, data: str) -> Tuple[str, int]:
    qidinfo: QidData = QidTable[qid]
    qiddir: str = qidinfo.fname

    if qidinfo.isdir: return "", Error.EOPENWRF.value

    qid_server_recv = qiddir + "/recv"
    unix_wrres = await write_pipe(qid_server_recv, data)
    if unix_wrres < 0:
        return "", unix_wrres

    # Reading a directory has (sadly) been relegated
    # to stat. Doing the thing.
    qid_server_send = qiddir + "/send"
    return await read_pipe(qid_server_send)

