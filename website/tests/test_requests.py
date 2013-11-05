# -*- coding: utf-8 -*-
import collections
import urllib
import urlparse
import unittest2
import urllib2

import lxml.html

from openerp import tools

from . import cases

__all__ = ['load_tests', 'CrawlSuite']

class RedirectHandler(urllib2.HTTPRedirectHandler):
    """
    HTTPRedirectHandler is predicated upon HTTPErrorProcessor being used and
    works by intercepting 3xy "errors".

    Inherit from it to handle 3xy non-error responses instead, as we're not
    using the error processor
    """

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        if 300 <= code < 400:
            return self.parent.error(
                'http', request, response, code, msg, hdrs)

        return response

    https_response = http_response

class CrawlSuite(unittest2.TestSuite):
    """ Test suite crawling an openerp CMS instance and checking that all
    internal links lead to a 200 response.

    If a username and a password are provided, authenticates the user before
    starting the crawl
    """

    def __init__(self, user=None, password=None):
        super(CrawlSuite, self).__init__()

        self.opener = urllib2.OpenerDirector()
        self.opener.add_handler(urllib2.UnknownHandler())
        self.opener.add_handler(urllib2.HTTPHandler())
        self.opener.add_handler(urllib2.HTTPSHandler())
        self.opener.add_handler(RedirectHandler())
        self.opener.add_handler(urllib2.HTTPCookieProcessor())

        self._authenticate(user, password)
        self.user = user

    def _request(self, path):
        return self.opener.open(urlparse.urlunsplit([
            'http', 'localhost:%s' % tools.config['xmlrpc_port'],
            path, '', ''
        ]))

    def _authenticate(self, user, password):
        if user is None: return

        url = 'http://localhost:{port}/login?{query}'.format(
            port=tools.config['xmlrpc_port'],
            query=urllib.urlencode({
                'db': tools.config['db_name'],
                'login': user,
                'key': password,
            })
        )
        auth = self.opener.open(url)
        assert auth.getcode() < 400, "Auth failure %d" % auth.getcode()

    def _wrapped_run(self, result, debug=False):
        paths = collections.deque(['/'])
        seen = set(paths)

        while paths:
            url = paths.popleft()
            r = self._request(url)
            cases.URLCase(self.user, url, r).run(result)

            if r.info().gettype() != 'text/html':
                continue

            doc = lxml.html.fromstring(r.read())
            for link in doc.xpath('//a[@href]'):
                href = link.get('href')

                # avoid repeats, even for links we won't crawl no need to
                # bother splitting them if we've already ignored them
                # previously
                if href in seen: continue
                seen.add(href)

                parts = urlparse.urlsplit(href)

                if parts.netloc or \
                    not parts.path.startswith('/') or \
                    parts.path == '/web' or\
                    parts.path.startswith('/web/') or \
                    (parts.scheme and parts.scheme not in ('http', 'https')):
                    continue

                paths.append(href)

def load_tests(loader, base, _):
    base.addTest(CrawlSuite())
    # blog duplicate (&al?) are on links
    base.addTest(CrawlSuite('admin', tools.config['admin_passwd']))
    base.addTest(CrawlSuite('demo', 'demo'))
    return base
