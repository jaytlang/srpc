#!/bin/bash

LOGLEVEL=debug python3 -m srpc.client.connect --hostname 127.0.0.1 --port 8000 --certfile=./examples/srpc.crt --connection_point=srpc.sock --username username --password password
