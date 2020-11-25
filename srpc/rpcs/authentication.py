import json
from typing import NamedTuple, Sequence, List

from srpc.rpcs.message import Message

AUTHENTICATION_RPC_ID = 0

class Credentials(NamedTuple):
    username: str
    password: str

class RPCDescriptor(NamedTuple):
    rpc_id: int
    rpc_name: str

def create_auth_request(request_id: int, credentials: Credentials) -> Message:
    data = json.dumps(credentials._asdict())
    data_bytes = data.encode('utf8')
    return Message(rpc_id=AUTHENTICATION_RPC_ID, request_id=request_id, data=data_bytes)

def parse_auth_request(message: Message) -> Credentials:
    data = message.data
    assert message.rpc_id == AUTHENTICATION_RPC_ID, f"invalid RPC ID: {message.rpc_id}"
    data_json = json.loads(data)
    assert isinstance(data_json, dict)
    return Credentials(**data_json)

def create_auth_response(request_id: int, rpc_descriptors: Sequence[RPCDescriptor]) -> Message:
    rpc_descriptor_dicts: List[object] = []
    for rpc_descriptor in rpc_descriptors:
        rpc_descriptor_dicts.append(rpc_descriptor._asdict())
    data = json.dumps(rpc_descriptor_dicts)
    data_bytes = data.encode('utf8')
    return Message(rpc_id=AUTHENTICATION_RPC_ID, request_id=request_id, data=data_bytes)

def parse_auth_response(message: Message) -> Sequence[RPCDescriptor]:
    assert message.rpc_id == AUTHENTICATION_RPC_ID, f"invalid RPC ID: {message.rpc_id}"
    data = message.data
    data_json = json.loads(data)
    rpc_descriptors: List[RPCDescriptor] = []
    for rpc_descriptor in data_json:
        assert isinstance(rpc_descriptor, dict)
        rpc_descriptors.append(RPCDescriptor(**rpc_descriptor))
    return rpc_descriptors
