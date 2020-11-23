import dataclasses
import ssl
from typing import Sequence

@dataclasses.dataclass(frozen=True)
class SharedConfig:
    address: str
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
