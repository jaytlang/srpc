=============================
sRPC - a secure rpc framework
=============================

Traditional remote procedure call (RPC) frameworks  serve all RPC endpoints as
one operating system user -- a design that does not permit privilege separation 
nor follow the principle of least privileges. Unlike these frameworks, sRPC
introduces a security-focused RPC architecture that supports discretionary and
mandatory access control, spawns separate processes per each user, and benefits
from the Unix file-system design and security primitives.

This is the prototype implementation of sRPC, to complement the paper's
security analysis and performance measurements. This provides a simple
interface for monolithic servers to benefit from the principle of least
privileges, and a CLI to interact with the system as a test user.

Demonstration

To use this partially implemented prototype, do
	sudo pip install -r requirements.txt

Note: you may need to run the above as the superuser
depending on your setup, to make sure that the server
(which is run as root) sees everything properly.

Once done, simply go ahead with:
	sudo python3 -m examples.server &
	python3 -m examples.cli

Make sure you set up your template filesystem first, and change
the server to, well, serve it.

Enjoy, and beware the bugs. There might be a lot of them.
