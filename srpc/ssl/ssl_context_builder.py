import ssl
from typing import Optional

class SSLContextBuilder:
    def __init__(self, protocol: int, certfile: str, keyfile: Optional[str] = None):
        self._certfile = certfile
        self._keyfile = keyfile
        self._protocol = protocol

    def build_server(self) -> ssl.SSLContext:
        context = ssl.SSLContext(self._protocol)
        context.load_cert_chain(certfile=self._certfile, keyfile=self._keyfile)
        return context

    def build_client(self) -> ssl.SSLContext:
        context = ssl.SSLContext(self._protocol)
        context.load_verify_locations(self._certfile)
        context.verify_mode = ssl.CERT_REQUIRED
        return context
