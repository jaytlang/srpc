# named pipe management, at the lowest level.
# Responsible for cloning the template filesystem
# when needed, and orchestrating asynchronous
# writes and reads to the server application itself.

from srpc.nine.dat import Error
from typing import List, Tuple
import asyncio
import aiofile
import stat
import os

async def write_pipe(path: str, data: str) -> int:
    try:
        if not stat.S_ISFIFO(os.stat(path).st_mode): return Error.EBADPATH.value

        done : bool = False
        # This is going to break because the pipe isn't
        # seekable. After the write succeeds, gtfo accordingly
        async with aiofile.async_open(path, 'a') as f:
            await f.write(data + "\n")
            done = True
    except: 
        if done: return len(data)
        return Error.EOPENWRF.value

    return len(data)
    
async def read_pipe(path: str, count: int) -> Tuple[str, int]:
    try:
        if not stat.S_ISFIFO(os.stat(path).st_mode): return "", Error.EBADPATH.value
        data: str = ""
        async with aiofile.async_open(path, 'r') as f:
            data = await f.read(length = count)
    except: return "", Error.EOPENRDF.value

    return data, 0
