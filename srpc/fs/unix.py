# named pipe management, at the lowest level.
# Responsible for cloning the template filesystem
# when needed, and orchestrating asynchronous
# writes and reads to the server application itself.

import stat
import os

import aiofiles


from srpc.nine.dat import Error, RPCException

async def write_pipe(path: str, data: str) -> None:
    if not stat.S_ISFIFO(os.stat(path).st_mode):
        raise RPCException(Error.EBADPATH)
    done = False
    try:
        # This is going to break because the pipe isn't
        # seekable. After the write succeeds, gtfo accordingly
        async with aiofiles.open(path, 'a') as f:
            await f.write(data + "\n")
            done = True
    except OSError as ex:
        if done:
            return
        print("i am ded not big surprise")
        raise RPCException(Error.EOPENWRF) from ex

async def read_pipe(path: str) -> str:
    if not stat.S_ISFIFO(os.stat(path).st_mode):
        raise RPCException(Error.EBADPATH)
    try:
        async with aiofiles.open(path, 'r') as f:
            data = await f.readline()
        return data
    except OSError as ex:
        raise RPCException(Error.EOPENRDF) from ex
