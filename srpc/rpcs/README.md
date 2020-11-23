# RPCs

This submodule contains the generic `Message` data structure used by RPC endpoints.

RPC endpoint implementations are responsible for encoding and decoding to bytes. The framework handles the rest.

In addition, the `authentication.py` file defines the RPC used for authentication, as well as encoders and decoders.
It is the only RPC in the framework. Upon supplying valid credentials, it returns the list of RPCs that this user is
authorized to call
