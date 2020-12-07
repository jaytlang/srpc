# QID<->System logic
# Manage the mapping between QIDs
# and socket files.

import shutil
import os
import pwd
import grp
from typing import List, Dict

from srpc.fs.dat import QidData, Stat
from srpc.fs.unix import write_pipe, read_pipe
from srpc.nine.dat import Error, RPCException

ROOT_QID = 0

class Qid:
    def __init__(self) -> None:
        # qidcount 0 is reserved for the root at the moment
        # work around this by setting the initial count to 1
        self._qidcount = 1
        self._concount = 1
        self._qid_table: Dict[int, QidData] = {}

    @property
    def qid_table(self) -> Dict[int, QidData]:
        return self._qid_table

    # Initialization: clone the template filesystem
    # into a new tree of named pipes for a given user
    # This does NOT handle the ctl file
    def clone(self, fsroot: str) -> str:
        # Recurse through the filesystem on disk and
        # copy sockets into a tree. By default, this
        # winds up a directory above the fsroot in
        # a directory numbered by concount, as such...
        cloneroot = f"/srv/{self._concount}/"
        while os.path.isdir(cloneroot):
            self._concount += 1
            cloneroot = f"/srv/{self._concount}/"

        def all_templates(fsroot: str) -> List[str]:
            fpaths: List[str] = []
            for root, dirs, files in os.walk(fsroot):
                for dirname in dirs:
                    fpaths.append(os.path.join(root, dirname))
                for filename in files:
                    fpaths.append(os.path.join(root, filename))

            return fpaths

        # For every file in the directory here,
        # instantiate two named pipes with
        # the same name as that file, one for sending
        # and one for receiving.
        os.mkdir(cloneroot)
        for fpath in all_templates(fsroot):
            clonepath = fpath.replace(fsroot, cloneroot)
            # If we've got a directory
            # - mkdir
            # - register
            # - copystat
            # - chown
            if os.path.isdir(fpath):
                os.mkdir(clonepath)
                self.register_qid(clonepath, True)
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
                self.register_qid(clonepath, False)
                print("Registered pre-file", clonepath)

                os.mkfifo(clonepath + "/recv")
                os.mkfifo(clonepath + "/send")

                shutil.copystat(fpath, clonepath + "/recv")
                shutil.chown(
                        clonepath + "/recv",
                        user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                        group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                        )
                shutil.copystat(fpath, clonepath + "/send")
                shutil.chown(
                        clonepath + "/send",
                        user=pwd.getpwuid(os.stat(fpath).st_uid).pw_name,
                        group=grp.getgrgid(os.stat(fpath).st_gid).gr_name
                        )

        # Manually register the root directory
        # since os.walk won't cover it
        # Register this with the original fsroot perms.
        shutil.copystat(fsroot, cloneroot)
        shutil.chown(
                cloneroot,
                user=pwd.getpwuid(os.stat(fsroot).st_uid).pw_name,
                group=grp.getgrgid(os.stat(fsroot).st_gid).gr_name
                )

        self.register_qid(cloneroot[:-1], True, isroot = True)
        print("Registered", cloneroot[:-1])

        return cloneroot

    def qid_for_aname(self, fname: str) -> int:
        print("Checking", fname)
        for qid in self._qid_table:
            if self._qid_table[qid].fname == fname:
                return qid

        raise RPCException(Error.EBADPATH)

    def register_qid(self, path: str, isdir: bool, isroot: bool = False) -> None:
        # Pop the QID into the table, with
        # no associated writer/reader for the
        # time being.
        if not isroot:
            self._qid_table[self._qidcount] = QidData(path, isdir)
            self._qidcount += 1
        else:
            self._qid_table[0] = QidData(path, isdir)

    def stat_qid(self, qid: int) -> Stat:
        data = self._qid_table[qid]

        # Strip off the fsroot
        fsroot = self._qid_table[ROOT_QID]
        userpath = data.fname.replace(fsroot.fname, "/")

        children: List[str] = []
        try:
            if data.isdir:
                children = os.listdir(data.fname)
        except OSError as ex:
            raise RPCException(Error.EOPENRDF) from ex

        return Stat(qid, userpath, data.isdir, children)

    async def write_qid(self, qid: int, data: str) -> str:
        qidinfo = self._qid_table[qid]
        qiddir = qidinfo.fname

        if qidinfo.isdir:
            raise RPCException(Error.EOPENWRF)

        qid_server_recv = os.path.join(qiddir, "recv")
        await write_pipe(qid_server_recv, data)

        # Reading a directory has (sadly) been relegated
        # to stat. Doing the thing.
        qid_server_send = os.path.join(qiddir, "send")
        return await read_pipe(qid_server_send)
