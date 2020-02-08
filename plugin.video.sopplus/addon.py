# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
from kodi_six import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from routing import Plugin
import requests

addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo("name")


@plugin.route("/")
def root():
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(channel_list, url="http://chlist.sopplus.tv/v1/channels"), xbmcgui.ListItem("sopplus.tv - V1"), isFolder=True)
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(channel_list, url="http://chlist.sopplus.tv/v2/channels"), xbmcgui.ListItem("sopplus.tv - V2"), isFolder=True)
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route("/channel_list")
def channel_list():
    url = plugin.args["url"][0]
    list_items = []
    user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
    s = requests.Session()
    r = s.get(url, headers={"User-Agent": user_agent}, timeout=5, verify=False)
    r.raise_for_status()
    channels = r.json()
    for c in channels:
        if c["type"] == "public":
            li = xbmcgui.ListItem(c["name"])
            li.setProperty("IsPlayable", "true")
            li.setInfo(type="Video", infoLabels={"Title": c["name"], "mediatype": "video"})
            url = "plugin://script.tvbus.player/?url={0}".format(c["address"])
            list_items.append((url, li, False))
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.setContent(plugin.handle, "videos")
    xbmcplugin.endOfDirectory(plugin.handle)

if __name__ == "__main__":
    plugin.run(sys.argv)
