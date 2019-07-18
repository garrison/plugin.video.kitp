import six

import re

import requests
from requests.compat import urljoin, urlencode
from bs4 import BeautifulSoup

class VideoUrl(object):
    # FIXME: scrape other things too so we can show the info as the video is playing :)
    def __init__(self, url):
        self.url = url

class LinkInfo(object):
    # abstract base class.  is this even necessary?
    pass

class TalkInfo(LinkInfo):
    def __init__(self, frag, title, speaker=None, has_video=None, has_slides=None, icon=None, fanart=None):
        self.frag = frag
        self.title = title
        self.speaker = speaker
        self.has_video = has_video
        self.has_slides = has_slides
        self.icon = icon
        self.fanart = fanart

class EventInfo(LinkInfo):
    def __init__(self, frag, title, date=None, icon=None):
        self.frag = frag
        self.title = title
        self.date = date
        self.icon = icon

def full_url(frag):
    return u'http://online.kitp.ucsb.edu/online/{}'.format(frag)

def get_soup(url_fragment=u''):
    page = requests.get(full_url(url_fragment))
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html5lib")
    base = page.url.partition('online/')[2]
    return base, soup

def mystrip(z):
    return re.sub(r'\s+', ' ', z).strip()

def scrape_index(base, soup):
    rv = []
    for ul in soup.find_all('ul'):
        for thing in ul.find_all('a', href=True):
            event = {}
            event['frag'] = urljoin(base, thing['href'])
            event['title'] = mystrip(thing.text)
            if base != '': # the toplevel index does not include dates, so
                           # don't even try
                ns = thing.next_sibling
                if ns:
                    event['date'] = mystrip(ns.string)
            m = re.search(r'^([\w]+)/?$', event['frag'])
            if m is not None:
                progname = m.group(1)
                event['icon'] = full_url('{progname}/{progname}-logo.jpg'.format(progname=progname))
            rv.append(EventInfo(**event))
    return rv

def find_main_schedule_content(soup):
    attempt1 = soup.find(id='schedule')
    if attempt1:
        return attempt1
    attempt2 = soup.find(string=[u'Speaker', u'Speaker:', u'[Cam]'])
    if attempt2:
        return attempt2.find_parent('table')
    raise Exception('No content found')

def scrape_event(base, soup):
    rv = []
    for thing in find_main_schedule_content(soup).find_all('a', href=True):
        talk = {}
        s2 = list(thing.parent.previous_siblings)
        if len(s2) >= 1:
            talk['speaker'] = mystrip(s2[1].text.strip().replace('\n', u' \u2013 '))
        s = list(thing.strings)
        talk['title'] = mystrip(s[0])
        talk['has_video'] = u'[Cam]' in s
        talk['has_slides'] = u'[Slides]' in s
        talk['frag'] = urljoin(base, thing['href'])
        talk['icon'] = full_url('{frag}oh/01.jpg'.format(frag=talk['frag']))
        talk['fanart'] = full_url('{frag}tv/play_thumb.jpg'.format(frag=talk['frag']))
        rv.append(TalkInfo(**talk))
    return rv

def scrape(frag):
    base, soup = get_soup(frag)
    # Is it a video?
    video_urls = [a['href'] for a in soup.find_all('a', href=True) if "mp4" in a['href']]
    if video_urls:
        return VideoUrl(video_urls[0])
    # These indexes are straightforward to handle
    if base in ('', 'si-pgmsindex.html', 'si-minipindex.html', 'si-confindex.html'):
        return scrape_index(base, soup)
    # These things require a bit more specialized processing
    if base in ('si-publecindex.html', 'bblunch/', 'colloq/', 'teachersconfs/'):
        return None # not yet implemented
    # The only remaining option is an event page
    return scrape_event(base, soup)
