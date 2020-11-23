import logging
import os.path
from typing import Sequence

from srpc.server.authenticator import AuthenticatedClient
from srpc.rpcs.message import Message
from srpc.rpcs.authentication import RPCDescriptor
from srpc.config.config import RPCConfig

LOGGER = logging.getLogger(__name__)

class RPCHandler:
    def __init__(self, rpc_config: RPCConfig) -> None:
        self._rpc_id = rpc_config.rpc_id
        self._rpc_filepath = rpc_config.filepath
        self._rpc_name = os.path.basename(rpc_config.filepath)

    def get_authorized_security_groups(self) -> Sequence[int]:
        # TODO read the authorized security groups for this RPC from SELinux
        # Currently returning 1000 since that is what the authenticator returns for a dummy value
        return [1000]

    @property
    def rpc_id(self) -> int:
        return self._rpc_id

    @property
    def rpc_name(self) -> str:
        return self._rpc_name

    @property
    def rpc_descriptor(self) -> RPCDescriptor:
        return RPCDescriptor(rpc_id=self._rpc_id, rpc_name=self._rpc_name)

    def is_discoverable(self, client: AuthenticatedClient) -> bool:
        # Returns whether to return a descriptor for this RPC given the client
        return client.security_context in self.get_authorized_security_groups()

    async def make_request(self, client: AuthenticatedClient, message: Message) -> bytes:
        # TODO
        # Must downgrade to the correct security context
        # You will need to add a data structure to organize the selinux group threads, and share
        # this data structure among all RPC handlers
        # Must write to the socket file
        # When the response is available, return it
        # DO NOT BLOCK! Use asyncio sockets which are non-blocking
        # for now, just echoing
        LOGGER.info("Echoing message: %s", message)
        return message.data
