# Based loosely on plugin.video.example

import sys
from urllib import urlencode
from urlparse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmcaddon

import kitp_scrape


# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon()
i18n = addon.getLocalizedString


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


_handlers = {}

def handler(_type):
    def _handler(func):
        _handlers[_type] = func
        return func
    return _handler

# FIXME: instead of just returning a list, the scraper should also return some toplevel info about that the list actually is about!

@handler(list)
def view_list(result):
    xbmcplugin.setPluginCategory(_handle, 'xxx')
    xbmcplugin.setContent(_handle, 'videos') # ???
    for item in result:
        if isinstance(item, kitp_scrape.EventInfo):
            li = xbmcgui.ListItem(label=item.title)
            url = get_url(frag=item.frag)
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
        elif isinstance(item, kitp_scrape.TalkInfo):
            li = xbmcgui.ListItem(label=u'{0}: {1}'.format(item.speaker, item.title))
            url = get_url(frag=item.frag)
            is_folder = False
            li.setInfo('video', {
                'title': item.title,
                'mediatype': 'video',
            })
            li.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
        else:
            raise Exception
    xbmcplugin.endOfDirectory(_handle)

@handler(kitp_scrape.VideoUrl)
def view_video_url(result):
    play_item = xbmcgui.ListItem(path=result.url)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def frag(frag):
    result = kitp_scrape.scrape(frag)
    _handlers[type(result)](result)

def index():
    xbmcplugin.setPluginCategory(_handle, 'KITP Videos')
    xbmcplugin.setContent(_handle, 'videos') # ???
    toplevel_items = [
        ('Recent Talks, Programs and Conferences', ''),
        ('Programs', 'si-pgmsindex.html'),
        ('Miniprograms', 'si-minipindex.html'),
        ('Conferences', 'si-confindex.html'),
        #('Blackboard Lunches', 'bblunch'),
        #('Colloquia', 'colloq'),
        #('Public Lectures', 'si-publecindex.html'),
        #('Teachers\' Confs', 'teachersconfs/'),
    ]
    for (label, frag) in toplevel_items:
        li = xbmcgui.ListItem(label=label)
        url = get_url(frag=frag)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def router(paramstring):
    params = dict(parse_qsl(paramstring, keep_blank_values=True))
    if 'frag' in params:
        frag(**params)
    else:
        index(**params)

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
