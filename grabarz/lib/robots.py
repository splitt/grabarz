## -*- coding: utf-8 -*-
import unittest
import urllib, urllib2
from lxml import html

from grabarz import app

SEED_LIMIT = 20
IMDB_RATING_EDGE = 7.0
QUERY_ITEMS = ['1080p', '720p']
PAGE_LIMIT = 20

class ParseError(IOError):
    def __init__(self, reason):
        self.args = reason,
        self.reason = reason

    def __str__(self):
        return '<urlopen error %s>' % self.reason

class TorrentSiteRobot(object):
    """ Abstract class to scrapping information from HTML site """        
    base_url = ''
    titles_xpath = ''
    last_seed_xpath = ''
    paginate_param = ''
    query_param = ''    
    page_on_start = 0
    
    def make_url(self, **params):
        return self.base_url + '?' + urllib.urlencode(params)
                                
    def _scan_page(self, **params):
        app.logger.debug('Parsing page %s' % self.make_url)
        full_url = self.make_url(**params)        
        raw_page_content = urllib2.urlopen(full_url, timeout=5).read()                
        page = html.fromstring(raw_page_content)         
        titles = page.xpath(self.titles_xpath)
        seed_count = page.xpath(self.last_seed_xpath)
        if not seed_count:
            seed_count = int(seed_count[-1])
        
        if not titles or not seed_count:
            raise Exception('Cant parse page, propably site is down')
        return titles, seed_count                                 
    
    def get_movies(self):
        founded = []
        for query in QUERY_ITEMS:
            self.query = query
            self.current_page = self.page_on_start                          
            while True:
                params = {self.query_param : query, 
                          self.paginate_param : self.current_page}                    
                try:
                    extracted_titles, last_seed = self._scan_page(**params)                    
                except(ParseError):
                    app.logger.warning('Error while parsing frml from url %' %
                                       self.make_url()
                                       )
                except(urllib2.URLError):
                    app.logger.warning('Timeout connection from url %' %
                                       self.make_url()
                                       )                                        
                
                self.current_page +=1 
                founded.extend(extracted_titles)                
                
                if last_seed < SEED_LIMIT or self.current_page == PAGE_LIMIT:
                    break
                
                
class BtJunkieRobot(TorrentSiteRobot):
    base_url = 'http://btjunkie.org/search'
    titles_xpath = "//table[@class='tab_results'][1]//a[@class='BlckUnd']/text()[1]"
    last_seed_xpath = '//font[@color="#32CD32"]/text()'
    page_on_start = 1
    query_param = 'q'
    paginate_param = 'p'        
        
    
class PirateBuyRobot(TorrentSiteRobot):    
    base_url = 'http://thepiratebay.org/search/%s/%s/7/207'
    titles_xpath = '//a[@class="detLink"]/text()'
    last_seed_xpath = '//table[@id="searchResult"]//tr[30]/td[3]/text()'
    
    def make_url(self, **params):
        return self.base_url % (self.query, self.current_page)
    
    
class FlaskrTestCase(unittest.TestCase):

    def test_btjunkie(self):        
        PAGE_LIMIT = 2        
        result = BtJunkieRobot().get_movies()
        print result
                        
if __name__ == '__main__':
    unittest.main()
    