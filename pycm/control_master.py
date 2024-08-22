import os
import random
import signal
import string
import subprocess
import sys
import threading
import time
from typing import Any


class ControlMaster:
    host: str = ""
    status: str = ""
    master_socket: str = ""
    controldir: str = ""
    debug: bool = False
    masterpid: int = 0
    cmdpid: int = 0

    def __init__(
        self,
        hostname: str,
        master_socket: str = "",
        debug: bool = False,
    ):
        self.ifdebug("in init")
        self.host = hostname
        self.check_control_dir()
        self.stdout = ""
        self.stderr = ""
        if master_socket == "":
            rnd = "".join(random.choice(string.ascii_letters) for i in range(10))
            self.master_socket = self.controldir + "/" + rnd
        else:
            self.master_socket = self.controldir + "/" + master_socket
        self.debug = debug

    def ifdebug(self, args: str) -> None:
        if self.debug:
            print(args)

    def cmd(self, args: Any) -> int:
        self.ifdebug("in cmd: executing %s" % args)
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            self.cmdpid = p.pid
            retcode = p.wait()
            self.stdout = p.communicate()[0]
            if retcode < 0:
                print("in cmd: Child was terminated ", -retcode, file=sys.stderr)
        except OSError as e:
            print("in cmd: Execution failed: ", e, file=sys.stderr)
        return retcode

    def checkauth(self) -> bool:
        self.ifdebug("in checkauth")
        if not os.path.exists(self.master_socket):
            self.ifdebug("in checkauth: FAIL: NOFILE")
            return False
        status = self.cmd(["ssh", "-S", self.master_socket, "-O", "check", "go"])
        if status != 0:
            self.ifdebug("in checkauth: FAIL: NOCONN")
            return False
        return True

    def connect(self) -> bool:
        self.ifdebug("in connect")
        if self.checkauth():
            return True
        threading.Thread(
            target=self.cmd, args=(["ssh", "-fNMS", self.master_socket, self.host],)
        ).start()
        print("connecting", self.host)
        for i in range(0, 10):
            if self.checkauth():
                self.masterpid = self.cmdpid
                print("Success")
                return True
            print(".")
            sys.stdout.flush()
            time.sleep(1)
        print("Fail")
        self.masterpid = self.cmdpid
        print("masterpid = %s" % self.masterpid)
        if self.masterpid > 0:
            try:
                os.kill(self.masterpid, signal.SIGTERM)
            except OSError:
                pass
        return False

    def disconnect(self) -> bool:
        self.ifdebug("in disconnect")
        if not self.checkauth():
            return True
        status = self.cmd(["ssh", "-S", self.master_socket, "-O", "exit", "go"])
        if status == 0:
            return True
        else:
            print("in disconnect: Fail : %s" % status)
            return False

    def put(self, src: str, dst: str) -> bool:
        if not self.checkauth():
            return False
        self.ifdebug("in put")
        status = self.cmd(
            ["scp", "-o controlpath=" + self.master_socket, src, "go:" + dst]
        )
        if status == 0:
            return True
        else:
            print("in put: Fail : %s" % status)
            return False

    def get(self, src: str, dst: str) -> bool:
        if not self.checkauth():
            return False
        self.ifdebug("in get")
        status = self.cmd(
            ["scp", "-o controlpath=" + self.master_socket, "go:" + src, dst]
        )
        if status == 0:
            return True
        else:
            print("in get: Fail : %s" % status)
            return False

    def rput(self, src: str, dst: str) -> bool:
        if not self.checkauth():
            return False
        self.ifdebug("in rput")
        status = self.cmd(
            ["scp", "-r", "-o controlpath=" + self.master_socket, src, "go:" + dst]
        )
        if status == 0:
            return True
        else:
            print("in rput: Fail : %s" % status)
            return False

    def rget(self, src: str, dst: str) -> bool:
        if not self.checkauth():
            return False
        self.ifdebug("in rget")
        status = self.cmd(
            ["scp", "-r", "-o controlpath=" + self.master_socket, "go:" + src, dst]
        )
        if status == 0:
            return True
        else:
            print("in rget: Fail : %s" % status)
            return False

    def exe(self, command: str) -> bool | int:
        self.ifdebug("in exe")
        if not self.checkauth():
            return False
        status = self.cmd(["ssh", "-S", self.master_socket, "go", command])
        if status == 0:
            print(self.stdout)
            return status
        else:
            print("in exe: Fail : %s" % status)
            return False

    def check_control_dir(
        self,
        controldir: str = os.environ["HOME"] + "/.controlmaster",
    ) -> None:
        self.ifdebug("in check_control_dir : controldir = %s" % controldir)
        if not os.path.isdir(controldir):
            os.makedirs(controldir)
        self.controldir = controldir


__all__ = [
    "ControlMaster",
]
