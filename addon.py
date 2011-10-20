# -*- coding: utf-8 -*-

# Debug
Debug = False

# Imports
import re, urllib, urllib2, simplejson, datetime, BeautifulSoup
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

__addon__ = xbmcaddon.Addon(id='plugin.audio.google.listen')
__info__ = __addon__.getAddonInfo
__plugin__ = __info__('name')
__version__ = __info__('version')
__icon__ = __info__('icon')
__fanart__ = __info__('fanart')
__path__ = __info__('path')
__cachedir__ = __info__('profile')
__language__ = __addon__.getLocalizedString
__settings__ = __addon__.getSetting
__set_settings__ = __addon__.setSetting

#SEARCH_URL = 'http://lfe-alpo-gm.appspot.com/search?q=%s&n=100'
SEARCH_URL = 'http://lfe-alpo-gm.appspot.com/search?q=%s&start=0'
#POPULAR_URL = 'http://lfe-alpo-gm.appspot.com/popular'
SUBSCRIPTIONS_URL = 'http://www.google.com/reader/public/subscriptions/user/-/label/Listen%20Subscriptions'
SUBSCRIPTIONS_URL_ALL = 'http://www.google.com/reader/api/0/subscription/list?output=json&client=XBMC'
UNREAD_COUNT = 'http://www.google.com/reader/api/0/unread-count?all=true&output=json&client=XBMC'
NEW_ITEMS = 'http://www.google.com/reader/api/0/stream/contents/user/-/label/Listen%20Subscriptions?r=n&xt=user/-/state/com.google/read&refresh=true'
FEED_URL = 'http://www.google.com/reader/api/0/stream/contents/feed/%s?n=20&client=XBMC'
FEED_URL_MORE = 'http://www.google.com/reader/api/0/stream/contents/%s?n=20&client=XBMC&c=%s'
TOKEN_URL = 'http://www.google.com/reader/api/0/token'
EDIT_URL = 'http://www.google.com/reader/api/0/subscription/edit?client=XBMC'
AUTH_URL = 'https://www.google.com/accounts/ClientLogin'

class Main:
  def __init__(self):
    if ("action=list" in sys.argv[2]):
      self.LIST()
    elif ("action=search" in sys.argv[2]):
      self.LIST()
    elif ("action=mylist" in sys.argv[2]):
      self.MYLIST()
    elif ("action=add_remove" in sys.argv[2]):
      self.ADD_REMOVE()
    elif ("action=add" in sys.argv[2]):
      self.ADD()
    else:
      self.START()

  def START(self):
    if Debug: self.LOG('\nSTART function')
    if __settings__('google') == 'true':
      if Debug: self.LOG('\nGoogle subscription activated!')

      Directories = [{'title':'My subscriptions', 'action':'mylist'},
                     {'title':'Add New Subscriptions', 'action':'add'},
                     {'title':'Search', 'action':'search'}]
    else:
      if Debug: self.LOG('\nGoogle subscription inactive!')
      Directories = [{'title':'Search', 'action':'search'}]

    if __settings__('firststart') == 'true':
      self.FIRSTSTART()
    else:
      for i in Directories:
        listitem = xbmcgui.ListItem(i['title'], iconImage='DefaultFolder.png', thumbnailImage=__icon__)
        parameters = '%s?action=%s&title=%s' % (sys.argv[0], i['action'], i['title'])
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
      # Sort methods and content type...
      xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
      # End of directory...
      xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def LIST(self):
    if Debug: self.LOG('\nLIST function')
    if ("action=search" in sys.argv[2]):
      URL = SEARCH_URL % self.SEARCH()
    try:
      URL = FEED_URL % self.Arguments('url', unquote=False)
    except:
      URL = FEED_URL_MORE % (self.Arguments('id', unquote=False), self.Arguments('page'))
    json = simplejson.loads(urllib.urlopen(URL).read())
    try:
      next_page = json['continuation']
      id = json['id']
    except:
      next_page = False
    for entry in json['items']:
      infoLabels = {}

      title = infoLabels['title'] = entry['title']
      try: infoLabels['plotoutline'] = entry['subtitle']
      except: infoLabels['plotoutline'] = ''
      try:
        try: infoLabels['plot'] = entry['summary']
        except: infoLabels['plot'] = entry['summary'][0]['content']
      except: infoLabels['plot'] = ''
      try:
        try: feedurl = entry['feed_url']
        except: feedurl = entry['origin'][0]['htmlurl']
      except: feedurl = ''
      print feedurl
      try:
        try: url = entry['enclosure_href']
        except: url = entry['enclosure'][0]['href']
      except: url = ''
      try: thumb = entry['image_href']
      except: thumb = __icon__
      try: infoLabels['author'] = entry['author']
      except: infoLabels['author'] = ''
      try: infoLabels['duration'] = str(entry['duration'])
      except: infoLabels['duration'] = str('')
      try:
        try: infoLabels['date'] = entry['date']
        except: infoLabels['date'] = datetime.datetime.fromtimestamp(int(entry['crawlTimeMsec']) / 1000).strftime('%d.%m.%Y')
      except: infoLabels['date'] = ''
      try:
        try: infoLabels['size'] = int(entry['enclosure_length'])
        except: infoLabels['size'] = int(entry['enclosure'][0]['length'])
      except: infoLabels['size'] = ''

      listitem = xbmcgui.ListItem(title, iconImage='DefaultVideo.png', thumbnailImage=thumb)
      listitem.setInfo(type='video', infoLabels=infoLabels)
      listitem.setProperty('IsPlayable', 'true')
      contextmenu = [('More Episodes', 'XBMC.RunPlugin(%s?action=list&url=%s)' % (sys.argv[0], urllib.quote_plus(FEED_URL % feedurl)))]
      if __settings__('google') == 'true':
        contextmenu += [('Subscribe', 'XBMC.RunPlugin(%s?action=add_remove&url=%s&ac=%s)' % (sys.argv[0], urllib.quote_plus(feedurl), 'subscribe'))]
      listitem.addContextMenuItems(contextmenu, replaceItems=False)
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(url, listitem, False)])
    if next_page:
      listitem = xbmcgui.ListItem('More...', iconImage='DefaultVideo.png', thumbnailImage=__icon__)
      parameters = '%s?action=list&id=%s&page=%s' % (sys.argv[0], urllib.quote_plus(id), next_page)
      xbmcplugin.addDirectoryItem(int(sys.argv[1]), parameters, listitem, True)
    # Sort methods and content type...
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    if infoLabels['date']:
      xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    if infoLabels['duration']:
      xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    if infoLabels['size']:
      xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_SIZE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def MYLIST(self):
    request = urllib2.Request(SUBSCRIPTIONS_URL)
    #request.add_data(urllib.urlencode(query_args))
    request.add_header('Authorization', 'GoogleLogin auth=%s' % self.AUTH())
    BeautifulSoup.BeautifulStoneSoup.NESTABLE_TAGS['outline'] = []
    soup = BeautifulSoup.BeautifulSOAP(urllib2.urlopen(request).read())
    for entry in soup.body.outline.findAll('outline'):
      title = entry['title']
      url = entry['xmlurl']
      thumb = 'http://lfe-alpo-gm.appspot.com/img?url=' + entry['xmlurl']
      listitem = xbmcgui.ListItem(title, iconImage='DefaultFolder.png', thumbnailImage=thumb)
      contextmenu = [('Unsubscribe', 'XBMC.RunPlugin(%s?action=add_remove&url=%s&ac=%s)' % (sys.argv[0], urllib.quote_plus(entry['xmlurl']), 'unsubscribe'))]
      listitem.addContextMenuItems(contextmenu, replaceItems=True)
      parameters = '%s?action=list&url=%s' % (sys.argv[0], urllib.quote_plus(url))
      xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(parameters, listitem, True)])
    # Sort methods and content type...
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
    # End of directory...
    xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

  def AUTH(self):
    if Debug: self.LOG('\nAUTH function')
    url = urllib2.Request(AUTH_URL)
    url.add_header('Content-Type', 'application/x-www-form-urlencoded')
    url.add_header('GData-Version', 2)
    data = urllib.urlencode({'Email': str(__settings__('gUser')),
                             'Passwd': str(__settings__('gPass')),
                             'service': 'reader',
                             'source': 'XBMC'})
    try:
      con = urllib2.urlopen(url, data)
      value = con.read()
      con.close()
      #print value
      result = re.compile('Auth=(.*)').findall(value)
      return result[0]
    except:
      if Debug: self.LOG('\nAuthorization error!')
      xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % ('Google Listen', 'Authorization error!'))

  def TOKEN(self):
    if Debug: self.LOG('\nTOKEN function')
    request = urllib2.Request(TOKEN_URL)
    request.add_header('Authorization', 'GoogleLogin auth=%s' % self.AUTH())
    try:
      con = urllib2.urlopen(request)
      result = con.read()
      con.close()
      return result
    except:
      if Debug: self.LOG('\nTOKEN error!')
      xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % ('Google Listen', 'Token error!'))

  def ADD_REMOVE(self, feed='', ac=''):
    if Debug: self.LOG('\nADD_REMOVE function')
    if feed == '':
      feed = self.Arguments('url')
    if ac == '':
      ac = self.Arguments('ac')
    #POST to add: s=$streams&t=$title&T=$token&ac=subscribe
    #POST to remove: s=$stream&T=$token&ac=unsubscribe
    #ADD = 'http://www.google.com/reader/api/0/subscription/quickadd?client=listen'
    query_args = {'a':'user/-/label/Listen Subscriptions',
                  's':'feed/' + feed,
                  'T':self.TOKEN(),
                  'ac':ac,
                  }
    request = urllib2.Request(EDIT_URL)
    request.add_data(urllib.urlencode(query_args))
    request.add_header('Authorization', 'GoogleLogin auth=%s' % self.AUTH())

    if urllib2.urlopen(request).read() == 'OK':
      if Debug: self.LOG('\n%s success' % ac)
      xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % ('Google Listen', '%s success' % ac))
      self.MYLIST()
    else:
      if Debug: self.LOG('\nError while %s' % ac)
      xbmc.executebuiltin('XBMC.Notification("%s", "%s")' % ('Google Listen', 'Error whlie %s' % ac))

  def SEARCH(self):
    if Debug: self.LOG('\nSEARCH function')
    kb = xbmc.Keyboard()
    kb.setHeading('Enter Search Term')
    kb.doModal()
    if (kb.isConfirmed()):
      text = kb.getText()
      return re.sub(' ', '+', text)
    else:
      self.START()

  def ADD(self):
    if Debug: self.LOG('\nADD function')
    kb = xbmc.Keyboard()
    kb.setHeading('Enter URL')
    kb.setDefault('http://')
    kb.doModal()
    if (kb.isConfirmed()):
      url = kb.getText()
      self.ADD_REMOVE(feed=url, ac='subscribe')
    else:
      self.START()

  def FIRSTSTART(self):
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno('Google Listen',
                       'Do you want to sign in your Google Account?',
                       'If you sing in, you can subscribe podcasts!')
    if ret:
      __addon__.openSettings()
      __set_settings__('firststart', 'false')
      self.START()
    else:
      __set_settings__('firststart', 'false')
      self.START()

  def Arguments(self, arg, unquote=True):
    Arguments = dict(part.split('=') for part in sys.argv[2][1:].split('&'))
    if unquote:
      return urllib.unquote_plus(Arguments[arg])
    else:
      return Arguments[arg]

  def LOG(self, description):
    xbmc.log("[ADD-ON] '%s v%s': '%s'" % (__plugin__, __version__, description), xbmc.LOGNOTICE)

if __name__ == '__main__':
  Main()
