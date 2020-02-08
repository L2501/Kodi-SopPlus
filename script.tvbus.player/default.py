# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from routing import Plugin

import re
import socket
import requests
from contextlib import closing

addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo("name")

ADDON_DATA_DIR = xbmc.translatePath(addon.getAddonInfo("path"))
RESOURCES_DIR = os.path.join(ADDON_DATA_DIR, "resources")
XBMC_TVBUS_SCRIPT = os.path.join(RESOURCES_DIR, "service", "tvbus.py")
TVBUS_SCRIPT = None


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@plugin.route("/")
def root():
    tvbus_url = plugin.args.get("url", [""])[-1]
    if tvbus_url:
        access_code = plugin.args.get("access_code", [""])[-1]
        timeout = int(plugin.args.get("timeout", ["90"])[-1])
        localport = int(plugin.args.get("localport", [find_free_port()])[-1])
        playerport = int(plugin.args.get("playerport", [find_free_port()])[-1])
        player_url = "http://127.0.0.1:{0}/mpegts_live".format(playerport)

        if xbmc.getCondVisibility("system.platform.android"):
            pass
        elif xbmc.getCondVisibility("system.platform.linux"):
            TVBUS_SCRIPT = XBMC_TVBUS_SCRIPT
        elif xbmc.getCondVisibility("system.platform.windows"):
            TVBUS_SCRIPT = XBMC_TVBUS_SCRIPT

        if TVBUS_SCRIPT:
            LIVE = False
            xbmc.executebuiltin(
                "RunScript({0},{1},{2},{3},{4},{5})".format(
                    TVBUS_SCRIPT, ADDON_DATA_DIR, tvbus_url, access_code, localport, playerport
                )
            )
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(plugin.name)
            session = requests.session()
            for i in range(timeout):
                pDialog.update(int(i / float(timeout) * 100))
                if pDialog.iscanceled():
                    break
                try:
                    _r = session.get(player_url, stream=True, timeout=1)
                    _r.raise_for_status()
                    LIVE = True
                    break
                except Exception:
                    xbmc.sleep(1000)

            session.close()
            pDialog.close()

            if LIVE:
                # wait 5 seconds for stream buffer
                xbmc.sleep(5 * 1000)
                li = xbmcgui.ListItem(path=player_url)
                xbmcplugin.setResolvedUrl(plugin.handle, True, li)
            else:
                xbmcplugin.setResolvedUrl(plugin.handle, False, xbmcgui.ListItem())
        else:
            li = xbmcgui.ListItem(path=tvbus_url)
            xbmcplugin.setResolvedUrl(plugin.handle, True, li)


if __name__ == "__main__":
    plugin.run(sys.argv)

