import wikipedia, query

__version__ = '$Id: revertbot.py 7131 2009-08-08 01:00:08Z alexsh $'

"""
    Copyright 2008 - Bryan Tong Minh
    Licensed under the terms of the MIT license.
"""

class BaseRevertBot(object):
    """ Base revert bot

    Subclass this bot and override callback to get it to do something useful.
    """
    def __init__(self, site, comment = None):
        self.site = site
        self.comment = comment

    def get_contributions(self, max = -1, ns = None):
        predata = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': '500',
            'ucuser': self.site.username(),
            'format': 'json'
        }
        if ns is not None: predata['ucnamespace'] = ns
        if max < 500 and max != -1: predata['uclimit'] = str(max)

        count = 0
        iterator = iter(xrange(0))
        never_continue = False
        while count != max or never_continue:
            try:
                item = iterator.next()
            except StopIteration:
                self.log(u'Fetching new batch of contributions')
                response, data = query.GetData(predata, self.site, back_response = True)
                if data.has_key('error'):
                    raise RuntimeError(data['error'])
                if data.has_key('query-continue'):
                    predata['uccontinue'] = data['query-continue']['usercontribs']
                else:
                    never_continue = True
                iterator = iter(data['query']['usercontribs'])
            else:
                count += 1
                yield item

    def revert_contribs(self, callback = None):
        self.site.forceLogin()

        if callback is None:
            callback = self.callback

        contribs = self.get_contributions()
        for item in contribs:
            try:
                if callback(item):
                    result = self.revert(item)
                    if result:
                        self.log(u'%s: %s' % (item['title'], result))
                    else:
                        self.log(u'Skipped %s' % item['title'])
            except StopIteration:
                return

    def callback(self, item):
        return 'top' in item

    def revert(self, item):
        predata = {
            'action': 'query',
            'titles': item['title'],
            'prop': 'revisions',
            'rvprop': 'ids|timestamp|user|content',
            'rvlimit': '2',
            'rvstart': item['timestamp'],
            'format': 'json'
        }
        response, data = query.GetData(predata, self.site, back_response = True)

        if data.has_key('error'):
            raise RuntimeError(data['error'])

        pages = data['query'].get('pages', ())
        if not pages: return False
        page = pages.itervalues().next()
        if len(page.get('revisions', ())) != 2: return False
        rev = page['revisions'][1]

        comment = u'Reverted to revision %s by %s on %s' % (rev['revid'],
            rev['user'], rev['timestamp'])
        if self.comment: comment += ': ' + self.comment

        page = wikipedia.Page(self.site, item['title'])
        page.put(rev['*'], comment)
        return comment

    def log(self, msg):
        wikipedia.output(msg)

