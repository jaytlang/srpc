# Examples

To run:
1. Go to the parent directory
2. In a terminal, run `python3 -m examples.server`
3. In another terminal, run `./examples/client.sh`
4. In a third terminal, run `python3 -m examples.consumer --connection_point=./srpc.sock`
The consumer should print out something like
```
RPC 1 response
b'hello, world 1'
RPC 2 response
b'hello, world 2'
```
Then exit