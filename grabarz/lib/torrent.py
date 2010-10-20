## -*- coding: utf-8 -*-
import urllib
import re

import pyrocore
from pyrocore.torrent import rtorrent
from grabarz import app

MB = 1024

def connect_rtorrent_api():
    """ Make connection to rotrrent via pyrocore library """
    
    #: monkey patch some config params
    pyrocore.config.rtorrent_rc = app.config['RTORRENT_CFG']
    pyrocore.config.xmlrpc = {}
    pyrocore.config.traits_by_alias = {
        'Debian'      : 'linux',
        'jamendo.com' : 'audio',
        }

    app.rtorrent = rtorrent.RtorrentEngine()

    # make connection at start
    app.rtorrent.open()


def tokenize(text, match=re.compile("([idel])|(\d+):|(-?\d+)").match):
    i = 0
    while i < len(text):
        m = match(text, i)
        s = m.group(m.lastindex)
        i = m.end()
        if m.lastindex == 2:
            yield "s"
            yield text[i:i+int(s)]
            i = i + int(s)
        else:
            yield s

def decode_item(next, token):
    if token == "i":
        # integer: "i" value "e"
        data = int(next())
        if next() != "e":
            raise ValueError
    elif token == "s":
        # string: "s" value (virtual tokens)
        data = next()
    elif token == "l" or token == "d":
        # container: "l" (or "d") values "e"
        data = []
        tok = next()
        while tok != "e":
            data.append(decode_item(next, tok))
            tok = next()
        if token == "d":
            data = dict(zip(data[0::2], data[1::2]))
    else:
        raise ValueError
    return data

def decode(text):
    try:
        src = tokenize(text)
        data = decode_item(src.next, src.next())
        for token in src: # look for more tokens
            raise SyntaxError("trailing junk")
    except (AttributeError, ValueError, StopIteration):
        raise SyntaxError("syntax error")
    return data

def get_torrent_data(src):
    """ Extracts movie filenames from torrent link """

    data = urllib.urlopen(src).read()
    return decode(data)
