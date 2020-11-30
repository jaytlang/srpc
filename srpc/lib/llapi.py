# Low level API...useful for the early
# client and other shim layers

# Basically, a catch all set of imports
# if you want to start messing with something
# like I did re. the test client

# 9P messages
from srpc.nine.dat import *
# LL messages
from srpc.srv.dat import Message
# Encoding those messages and vice versa
from srpc.srv.msg import *
