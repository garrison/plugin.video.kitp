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

@handler(kitp_scrape.List)
def view_list(result):
    if result.title:
        xbmcplugin.setPluginCategory(_handle, result.title)
    xbmcplugin.setContent(_handle, 'videos') # ???
    for item in result.items:
        if isinstance(item, kitp_scrape.EventInfo):
            abbr = item.frag.strip('/')
            full_title = u'{title} ({abbr})'.format(title=item.title, abbr=abbr)
            li = xbmcgui.ListItem(label=full_title)
            url = get_url(frag=item.frag)
            is_folder = True
            li.setInfo('video', {
                'title': full_title,
                'mediatype': 'video',
                'plot': abbr,
            })
            li.setArt({
                'icon': item.icon,
                'thumb': item.icon,
            })
            xbmcplugin.addDirectoryItem(_handle, url, li, is_folder)
        elif isinstance(item, kitp_scrape.TalkInfo):
            li = xbmcgui.ListItem(label=u'{0}: {1}'.format(item.speaker, item.title))
            url = get_url(frag=item.frag)
            is_folder = False
            li.setInfo('video', {
                'title': item.title,
                'mediatype': 'video',
                'plot': u'[UPPERCASE]{speaker}[/UPPERCASE][CR][CR][B]{title}[/B]'.format(speaker=item.speaker, title=item.title),
            })
            li.setArt({
                'fanart': item.fanart,
                'icon': item.icon,
                'thumb': item.icon,
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
