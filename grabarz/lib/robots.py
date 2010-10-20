## -*- coding: utf-8 -*-
from __future__ import with_statement

import os, logging
from os.path import split, join, getsize
import zipfile
import unittest
import difflib
import urllib, urllib2
from lxml import html
from copy import copy

import mechanize
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
    
    
#===============================================================================
# TORRENT SITE ROBOTS
#===============================================================================

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
    
    
#===============================================================================
# SUBTITLE DOWNLOADERS
#===============================================================================

def getsub_napisy24(path_to_file):
    #: get file size and name
    size = getsize(path_to_file)
    folder, filename = split(path_to_file)
    
    br = mechanize.Browser()    
    
    #: login    
    br.open('http://napisy24.pl/logowanie')
    br.select_form(nr=1)
    br['form_logowanieMail'] = 'splittor@tlen.pl'
    br['form_logowanieHaslo'] = 'zajonez'
    br.submit()    
         
    #: advenced search by file size    
    br.open('http://napisy24.pl/szukaj/zaawansowane/')
    
    #advanced search
    br.select_form(nr = 1)    
    br['form_szukajAdvRozmiar'] = str(size)    
    response = br.submit().read()
    page = html.fromstring(response)
    rows = page.xpath('//div[@class="fullWhiteBox"][2]//div[@id="defaultTable"]//tr')
    if not rows:
        return False
    
    _extract = lambda x: ''.join(copy(x).xpath('//strong/text()'))
        
    titles = [_extract(x) for x in rows[1::2]]
    matches = difflib.get_close_matches(filename, titles)
    
    if not matches:
        return False
            
    selected = [(_extract(x), y) for x, y in zip(rows[1::2],rows[2::2]) 
                        if _extract(x) == matches[0]][0][1]    
    
    href = copy(selected).xpath('//a')[0].attrib['href']
    link = br.find_link(url_regex=href)
    zip_data = br.follow_link(link).read()
    zip_file_path = join(folder, 'napisy24sub.zip')
    with open(zip_file_path,'w') as zip_file:
        zip_file.write(zip_data)
        
    #: extracting
    z = zipfile.ZipFile(zip_file_path, mode='r')
    name = z.namelist()[0]
    z.extractall(folder)
    z.close()
    os.rename(join(folder, name), join(folder, split(filename)[0]+'_n24.txt'))
    #: removing all zip
    os.remove(zip_file_path)
    
    logging.debug('Succesfully download and unzipped n24 '
                  'subtitles for item: %s'% filename)    
    return True

    
class FlaskrTestCase(unittest.TestCase):

    def test_btjunkie(self):        
        PAGE_LIMIT = 2        
        result = BtJunkieRobot().get_movies()
        print result
                        
if __name__ == '__main__':
    getsub_napisy24('/home/mzajonz/movies/The.Vampire.Diaries.S02E03.Bad.Moon.Rising.HDTV.XviD-FQM.avi')
#    unittest.main()
    