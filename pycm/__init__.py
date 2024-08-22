import sys

from pycm.master_connection import MasterConnection
from pycm.slave_connection import SlaveConnection

__all__ = [
    "MasterConnection",
    "SlaveConnection",
]

if __name__ == "__main__":
    assert len(sys.argv) > 1
    host = sys.argv[1]
    if len(sys.argv) > 2:
        debug = sys.argv[2] in ["True", "true", "1"]
    else:
        debug = False
    ssh = SecondaryConnection(host, debug=debug)
    ssh.connect()
    ssh.exe("uptime")
    ssh.disconnect()
