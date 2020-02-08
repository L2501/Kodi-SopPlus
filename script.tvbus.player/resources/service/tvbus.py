# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import stat
import shutil
import sys
import subprocess
import platform

from xbmc import Monitor, Player
from kodi_six import xbmc

CREATE_NO_WINDOW = 0x08000000


class TvbusPlayer(Player):
    def __init__(self):
        Player.__init__(self)
        self.ended = False
        self.started = False

    def onPlayBackStarted(self):
        self.started = True

    def onPlayBackError(self):
        self.ended = True

    def onPlayBackEnded(self):
        self.ended = True

    def onPlayBackStopped(self):
        self.ended = True


class TvbusMonitor(Monitor):
    def __init__(self, engine, env, tvbus_url, access_code, localport, playerport):
        Monitor.__init__(self)
        self.player = TvbusPlayer()
        self.env = env
        if type(engine) == list:
            self.engine = engine
        else:
            self.engine = [engine]
        self.localport = localport
        self.playerport = playerport
        self.tvbus_url = tvbus_url
        self.access_code = access_code
        self.running = False

    def run(self):
        self.start_tvbus()
        pre_start = 0
        # non-service addons do not recieve abort signal
        while not self.abortRequested():
            if not self.player.started:
                pre_start +=1
                if pre_start >=100:
                    break
            if self.player.ended:
                break
            self.waitForAbort(1)
        self.stop_tvbus()

    def start_tvbus(self):
        if self.access_code:
            command = self.engine + ["init", self.localport, self.playerport]
            if self.env:
                self.tvbus = subprocess.Popen(command, env=self.env, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            else:
                self.tvbus = subprocess.Popen(command, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            pre_init = 0
            # non-service addons do not recieve abort signal
            while not self.abortRequested():
                output = self.tvbus.stdout.readline()
                if output.startswith("[Inited]"):
                    self.tvbus.stdin.write("start -c {0} {1}\n".format(self.access_code, self.tvbus_url))
                    break
                if self.player.ended or self.tvbus.poll() is not None:
                    break
                pre_init +=1
                if pre_init >=100:
                    break
                self.waitForAbort(1)
        else:
            command = self.engine + [self.tvbus_url, self.localport, self.playerport]
            if self.env:
                self.tvbus = subprocess.Popen(command, env=self.env)
            else:
                self.tvbus = subprocess.Popen(command, creationflags=CREATE_NO_WINDOW)
        self.running = True
        print("running")

    def stop_tvbus(self):
        print("kill")
        try:
            # terminate does not work
            self.tvbus.kill()
            # prevent GC zombies
            self.tvbus.wait()
            self.running = False
        except OSError:
            # process already dead
            pass


def log(msg):
    xbmc.log("[Tvbus] {0}".format(msg), level=xbmc.LOGNOTICE)


def is_exe(fpath):
    if os.path.isfile(fpath):
        if not os.access(fpath, os.X_OK):
            st = os.stat(fpath)
            os.chmod(fpath, st.st_mode | stat.S_IEXEC)


def test_exe(engine, env=None):
    is_exe(ENGINE)
    if env:
        process = subprocess.Popen(engine, env=env, stdout=subprocess.PIPE)
    else:
        process = subprocess.Popen(engine, stdout=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
    info = process.stdout.readline()
    log(info)
    process.wait()


if __name__ == "__main__":
    ADDON_DATA_DIR = sys.argv[1]
    LINUX_x86_64_TVBUS = os.path.join(ADDON_DATA_DIR, "resources", "tvbus", "bin", "linux_x86_64", "tvbus")
    WIN_32_TVBUS = os.path.join(ADDON_DATA_DIR, "resources", "tvbus", "bin", "win32", "tvbus.exe")
    ENGINE = None

    tvbus_url = sys.argv[2]
    access_code = sys.argv[3]
    localport = sys.argv[4]
    playerport = sys.argv[5]

    if xbmc.getCondVisibility("system.platform.android"):
        pass
    elif xbmc.getCondVisibility("system.platform.linux"):
        if "x86_64" == platform.machine():
            ENV = os.environ.copy()
            ENGINE = LINUX_x86_64_TVBUS
            test_exe(ENGINE, ENV)
    elif xbmc.getCondVisibility("system.platform.windows"):
        ENV = None
        ENGINE = WIN_32_TVBUS
        test_exe(ENGINE)

    if ENGINE:
        TvbusMonitor(ENGINE, ENV, tvbus_url, access_code, localport, playerport).run()

