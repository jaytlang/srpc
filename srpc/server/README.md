# Server

The main RPC server

`server.py` is the main entrypoint. It creates an instance of the `authenticator`, a `rpc_handler` for each RPC endpoint, and an `rpc_server` to serve the RPCs.

It uses async python which allows one thread to serve all RPCs.

The `rpc_handler` is responsible for ensuring that the RPC is called under the correct security context.