# Configuration file

import os

class Config(object):
    """
    Setting SECRET_KEY to get forms CSRF to work.  Randomly
    generating is probably not a good idea if running
    in production.
    """
    SECRET_KEY = os.urandom(24)
    SESSION_TYPE = "filesystem"


