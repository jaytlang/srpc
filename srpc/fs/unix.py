# named pipe management, at the lowest level.
# Responsible for cloning the template filesystem
# when needed, and orchestrating asynchronous
# writes and reads to the server application itself.

from typing import Tuple
import stat
import os

import aiofiles


from srpc.nine.dat import Error

async def write_pipe(path: str, data: str) -> int:
    done = False
    try:
        if not stat.S_ISFIFO(os.stat(path).st_mode):
            return Error.EBADPATH.value

        # This is going to break because the pipe isn't
        # seekable. After the write succeeds, gtfo accordingly
        async with aiofiles.open(path, 'a') as f:
            await f.write(data + "\n")
            done = True
    except OSError:
        if done:
            return len(data)
        print("i am ded not big surprise")
        return Error.EOPENWRF.value

    return len(data)

async def read_pipe(path: str) -> Tuple[str, int]:
    try:
        if not stat.S_ISFIFO(os.stat(path).st_mode):
            return "", Error.EBADPATH.value
        async with aiofiles.open(path, 'r') as f:
            data = await f.readline()
        return data, 0
    except OSError:
        return "", Error.EOPENRDF.value
