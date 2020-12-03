========================
sRPC - electric boogaloo
========================

Work in progress. See examples/ for
a client REPL and a server application
leveraging listen/announce. Source is
heavily annotated.

This is the multiuser tree. I'm attempting
to do the following here, in order:

-> Separate this subsystem into two executables,
   one for the main server itself (which handles
   auth and attach 9P requests) and a new lazily
   allocated executable for each context. /srv/ctl
   should be utilized (which iirc we already have
   support for this) here to set up unix domain
   sockets (since the server is not a wildcard
   anymore, obviating pipes) under asyncio.

-> Once this is done preserving original functionality,
   write a shim program which lowers its own permissions
   to specified values before exec'ing the main body.
   this avoids troubles with fork() asyncio deals with

-> done.
