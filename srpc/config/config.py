import dataclasses
from typing import Sequence, Optional

@dataclasses.dataclass(frozen=True)
class SharedConfig:
    hostname: str
    port: int
    ssl_version: int
    certfile: str

@dataclasses.dataclass(frozen=True)
class RPCConfig:
    filepath: str
    rpc_id: int

@dataclasses.dataclass(frozen=True)
class ServerConfig:
    shared: SharedConfig
    keyfile: str
    rpcs: Sequence[RPCConfig]

@dataclasses.dataclass(frozen=True)
class ClientConfig:
    shared: SharedConfig
    socket_filepath: str
    username: str
    password: str

     # set to None for all RPCs
     # or specify the explicit list of RPCs that this client can call
    rpcs: Optional[Sequence[int]] = None
