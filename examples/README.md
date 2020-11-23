# Examples

To run:
1. Go to the parent directory
2. In a terminal, run `python3 -m examples.server`
3. In another terminal, run `python3 -m examples.client`
The client should print out something like
```
RPC 1 response
Message(rpc_id=1, request_id=0, data=b'hello, world 0')
RPC 2 response
Message(rpc_id=1, request_id=1, data=b'hello, world 1')
```
Then exit