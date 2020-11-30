# Data structures for the authentication end
# of the server side.

# We won't internally represent afids as
# files on our end since that's just riddled
# with overhead, but we will implement their
# functionality through in-RAM data structures.

# In the future, with a proper aqid implementation,
# users could write their own auth modules and plug
# them in, allowing the afid/qid to serve as a secure
# auth channel provided the connection is encrypted

# Unlike the normal fids (operating under the one
# con one user assumption for proof of concept) the
# afids are truly global. To prevent someone from
# striking gold, it's recommended you clunk these
# when you're done, and also the reason why you
# need a uname to attach even if you present a
# valid afid. Furthermore, it's recommended you
# clunk these when you're done with them.

from typing import NamedTuple, Dict

class AFidData(NamedTuple):
    uname: str
    aname: str

AFidTable: Dict[int, AFidData] = {}
AFidValidity: Dict[int, bool] = {}
