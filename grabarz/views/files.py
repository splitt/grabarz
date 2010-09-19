## -*- coding: utf-8 -*-
from __future__ import with_statement

import re
import os
import shutil
from os.path import join, split
import ConfigParser
from copy import deepcopy
from datetime import date

import mechanize
from imdb import IMDb
from flask import Module, request

from grabarz import app, models, common
from grabarz.lib import torrent, beans, utils

imdb = IMDb()
files = Module(__name__)
IMDB_ICO = '<img src="/static/_imdb.png">'
FILMWEB_ICO = '<img src="/static/_filmweb.ico">'

MENU_OPTIONS = [
    ('refresh', beans.MenuItem(
                    label = "odśwież dane",
                    icon = "icon-arrow_refresh",
                    link = dict(
                        url = "/files/refresh%s",
                        slot = "CONTENT",               
                    ),
                ),
    ),
    
    ('start_downloading', beans.MenuItem(
                            label = "Zacznij pobieranie",
                            icon = "icon-television_delete",
                            link = dict(
                                url = "/files/move_watched%s",
                                slot = "CONTENT",               
                            )
                        ),
    ),    
    
    ('move_watched', beans.MenuItem(
                        label = "przenieś do obejrzanych",
                        icon = "icon-arrow_down",
                        link = dict(
                            url = "/files/move_watched%s",
                            slot = "CONTENT",               
                        )
                    ),
    ),
    
    ('move_ready', beans.MenuItem(
                        label = "przenieś do gotowych",
                        icon = "icon-eye",
                        link = dict(
                            url = "/files/move_ready%s",
                            slot = "CONTENT",               
                        )
                    ),
    ),
    
    ('separator', dict(type = 'separator')),
        
    ('delete', beans.MenuItem(
                    label = "Usuń z dysku",
                    icon = "icon-delete",
                    link = dict(
                        url = "/files/delete%s",
                        slot = "CONTENT",               
                    )
                ),
    ),            
]


MOVIE_DATA = dict(
        imdb_rating = '',
        imdb_data = '',
        title = '',
        runtime = '',
        year = '',
        date_added = '',
        filmweb_rating = '',
        filmweb_opinions = '',
        filmweb_url = '',
        polish_title = '',
    )


@files.route('/files/window-movies')
@common.jsonify
def window_movies():
    """ Main movies window """
    return beans.Window(
        heading = 'filmy',
        height = 0.8,
        width = 0.9,
        object = beans.Tabs(
            heading = None,
            tabs = [
                beans.Tab(                    
                    id = 'movies-ready',
                    url = '/make_slot?url=/files/ready',
                    title = 'Gotowe do obejrzenia',
                    params = dict(
                      icon = 'icon-eye',    
                    ),
                ),
                beans.Tab(
                    id = 'movies-downloading',
                    url = '/make_slot?url=/files/downloading',
                    title = 'Pobierane',
                    params = dict(
                      icon = 'icon-arrow_down',            
                    ),                    
                ),                
                beans.Tab(
                    id = 'movies-founded',
                    url = '/make_slot?url=/files/founded',
                    title = 'Znalezione',
                    params = dict(
                      icon = 'icon-zoom',            
                    ),                    
                ),
                beans.Tab(
                    id = 'movies-watched',
                    url = '/make_slot?url=/files/watched',
                    title = 'Obejrzane',
                    params = dict(
                      icon = 'icon-television_delete',            
                    ),                    
                ),
            ]        
        )                        
    )
    

 
@files.route('/files/feed_movie')
@common.jsonify
def feed_movie():
    """Creates folder with movie data."""
                
    path = request.args.get('path')
    file = request.args.get('file')
    
    #: if file passed than adding now torrent, otherwise only refreshing
    title = file or path.split('/')[-1]
    
    hydra_log = HydraLog('feeding_log|'+title, 
                         "Pobieranie definicji filmu '%s'" % title)
    
    hydra_log.emit(u'Rozpoczynam procesowanie filmu "%s" ' % title)        
    data = dict(MOVIE_DATA)  
            
    #: Parsing movie filename for proper title
    if file:
        year_re = '(1|2)[0-9]{3}$'
        title = title.replace('.', ' ')
        title = re.sub('(1080|720).*$', '', title).strip()
        title = re.sub('\(|\)|\[|\]', '', title).strip()        
        title = re.sub(year_re, '', title).strip().capitalize()
        hydra_log.emit(u'Sparsowano tytuł filmu: "%s"' % title)
        movie_year = re.search(year_re, title)
        
        if movie_year:
            movie_year = movie_year[0]
            hydra_log.emit(u'Wyciągnięto rok produkcji z nazwt filmu: %s' 
                           % movie_year)
        
    else: #refreshing
        config = ConfigParser.RawConfigParser()        
        config.read(join(path, 'grabarz.ini'))
        ini_data = dict(config.items('data'))
        movie_year = ini_data.get('year')
        title = ini_data.get('title')        
        
                
    config = ConfigParser.RawConfigParser()
    
                            
    #: Searching in IMDB database    
    hydra_log.emit(u'Szukam definicji w bazie IMDB')    
    try:
        movie = imdb.search_movie(title)[0]
    except IndexError:
        app.logger.debug(u'Nie rozpoznano filmu "%s" w bazie IMDB' % title)
        return    
        
    imdb_id = movie.getID()
    imdb_data = imdb.get_movie(imdb_id)
    title = data['title'] = imdb_data['title']
    hydra_log.emit(u'Znaleziono film "%s" w bazie IMDB' % title)
        
    #: Make contener directory for files
    full_work_dir = join(app.config['MOVIES_DOWNLOADING_DIR'], title)
    
    try:    
        os.makedirs(full_work_dir)
    except OSError:
        pass #: Path propably exists 
    
    #: Creating a ghost file
#    file = open(join(full_work_dir, name+'_downloading'), 'w')
#    file.close()    
        

    data['imdb_rating'] = imdb_data.get('rating')
    data['runtime'] =  ' '.join(imdb_data.get('runtime')[:1])
    data['year'] =  imdb_data.get('year')
    data['genres'] = ' '.join(imdb_data.get('genres'))
    data['date_added'] = '-'.join(str(date.today()).split('-')[::-1])
                
    #: Saving cover url
    if imdb_data.get('cover url'):    
        download(imdb_data['cover url'], join(full_work_dir, 'cover.jpg'))
                     
    #: Searching in Filmweb site
    hydra_log.emit(u'Szukam definicji w bazie Filmweb')
    br = mechanize.Browser()
    resp = br.open('http://www.filmweb.pl/search?q=%s' % title.replace(' ','+'))
    
    #: Dodge Welcome commercial  :)
    try:        
        resp = br.follow_link(text_regex=u"Przejd", nr=0)
    except(mechanize.LinkNotFoundError):
        resp = None
                
    #: Get first record from search results
    try:
        pred = lambda link:dict(link.attrs).get('class') == u'searchResultTitle'        
        resp = br.follow_link(predicate = pred)
    except(mechanize.LinkNotFoundError, KeyError):        
        resp = None        
    
    if resp:
        hydra_log.emit(u'Znaleziono film "%s" w bazie Filmweb' % title)
        d = pq(resp.read())
        data['filmweb_rating'] = d('.rating .average').text().replace(',', '.')
        data['description'] = d('.filmDescrBg').text()
        data['filmweb_url'] = br.geturl()
        data['polish_title'] = d('.fn').text()
        data['filmweb_opinions'] = '\n'.join(d('.fltTitle')
                                        .text().split('czytaj dalej'))
    else:
        app.logger.warning(u'Nie znaleziono filmu "%s" w bazie Filmweb' % title)    
        
    data['__space__'] = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    hydra_log.emit(u"""=================================<br/>
                        Podstawowe informację o filmie:<br/> 
                        %(__space__)srating IMDB: %(imdb_rating)s<br/>
                        %(__space__)sFilmweb: %(filmweb_rating)s<br/>
                        %(__space__)sPolski tytuł: "%(polish_title)s"<br/>
                        %(__space__)srok produkcji: %(year)s<br/>                       
                    """% data) 
            
    #: Dumps data to ini file    
    config.add_section('data')
    for k, v in data.items():
        val = unicode(v).encode('utf-8')
        config.set('data', k, val)
        
    with open(join(full_work_dir, 'grabarz.ini'), 'wb') as configfile:
        config.write(configfile)
        
    hydra_log.emit(u'Utworzono plik ini<br/><br/>KONIEC')
    
    models.CallbackUpdate(beans.Reload(slot = "CONTENT")).commit()
    hydra_log.close()
    
    return 'done'
            
    

def get_movies_list(path, menu_options,title = None):
    """ Listing movies for given path in filesystem """    
    data = []
    config = ConfigParser.RawConfigParser()
    
    #: Extract data from ini files
    for i, dir in enumerate( os.listdir(path)):                            
        dir_path = join(path, dir) 
        config.read(join(dir_path, 'grabarz.ini'))
        d = dict(config.items('data'))
        
        d = dict( (k, v.decode('utf-8')) for k, v in d.items())
        ratings = '%s Imdb: <b>%s</b></span></br>' % (IMDB_ICO, d['imdb_rating'])
        
        imdb_rating = average = float(d['imdb_rating'])
        
        if d.get('filmweb_rating'):
            ratings += u''.join([
                '<a target="_blank" href="%s">' % d['filmweb_url'],
                '<span> %s Filmweb:' % FILMWEB_ICO,
                '<b>%s</b></span></a></br>' % d['filmweb_rating'] 
            ])
            
            
            filmweb_rating = float(d.get('filmweb_rating')) 
                        
            average = str((imdb_rating + filmweb_rating) / 2)
                        
        ratings = (
            '<!--%s-->' % average + 
            u'<span class="average"> Średnia: %s</span></br>' % average +
            ratings
        )
                
        d['ratings'] = ratings
             
        d['title'] = '<br/>'.join([
            u"<span class='title'>%s (%s)</span>" % \
                (d['title'], d.get('polish_title') or ''), 
            '<b>Rok produkcji:</b> %s ' % d['year'],
            '<b>Czas:</b> %s minut '% d['runtime'],
            '<b>Gatunki</b> %s' % d['genres'],            
            (d.get('description') or '')[:700],            
        ])
        
        d['cover'] = '<img src="%s"/>' % join('_MOVIES_DIR',split(path)[-1], 
                                              dir, 'cover.jpg')
        d['__params__'] = dict(
            style = 'movie_row',
            uid = dir_path,
            )    
        data.append(d)
        
    menu_options = ','.join(menu_options)
                
    return beans.Composite(beans.Listing(
         heading=title,
         paging = False,         
         menu_url = '/files/get_context_menu?items=%s' % menu_options,
         autoexpand_column = "title",
         param_name = 'uid',
         columns=[
            dict(
                 renderer = 'numberer',
            ),
            dict(
                 renderer = 'checkbox',
            ),            
            dict(
                 width="100",
                 title="Plakat",
                 id="cover",
            ),                              
            dict(
                 width="500",
                 title="Tytuł",
                 id="title",
                 sortable = "true",
            ),
            dict(
                 width="100",
                 title="Oceny",
                 id="ratings",
                 sortable = "true",
            ),                  
            dict(
                 width="60",
                 title="Data dodania",
                 id="date_added",
                 sortable = "true",
            ),
#            dict(
#                 width="50",
#                 title="Napisy",
#                 id="subtitles",
#                 sortable = "false",
#            ),
        ],
        data=data,
    ))


@files.route('/files/ready')
@common.jsonify
def ready():
    """ Displays list of downloaded movies """
    return get_movies_list(path = app.config['MOVIES_READY_DIR'],
                           menu_options = ['refresh', 'delete', 
                                           'separator','move_watched'])


@files.route('/files/downloading')
@common.jsonify
def downloading():
    """ Displays list of current downloading movies """
    return get_movies_list(path = app.config['MOVIES_DOWNLOADING_DIR'],
                           menu_options = ['refresh','separator', 'delete'])
    

@files.route('/files/founded')
@common.jsonify
def founded():
    """ Displays list of founded movies by robots """
    return get_movies_list(path = app.config['MOVIES_FOUND_DIR'],
                           menu_options = ['refresh', 'start_downloading', 
                                           'separator','delete',]
                           )
    
    
@files.route('/files/watched')
@common.jsonify
def watched():
    """ Displays list of watched movies """
    return get_movies_list(path = app.config['MOVIES_WATCHED_DIR'],
                           menu_options = ['refresh', 'separator', 
                                           'move_ready', 'delete'])    
    
        
@files.route('/files/fetch-torrent-file', methods=['GET', 'POST'])
@common.jsonify
def fetch_torrent_file():
    """ Reads information from torrent file and creates grabarz.ini 
    file for given movie."""
    
    file = torrent.get_torrent_filenames(request.form['torrent_src'])[0]        
    path = join(app.config['MOVIES_DOWNLOADING_DIR'], 'movies')
    models.Task('/files/feed_movie?file=%s&path=%s' % (file, path)).commit()
    return beans.Null()
    

@files.route('/files/get_context_menu', methods=['GET', 'POST'])
@common.jsonify
def get_context_menu():
    """ Filter specific menu options from all possible values. 
    Options are given in URL param. 
    """
    arg_options = request.args['items'].split(',')     
    menu_options = []
    

    for name, option in deepcopy(MENU_OPTIONS):
        if name in arg_options:
            if option.get('link'):
                option['link']['url'] = option['link']['url'] % post2get()
            menu_options.append(option)
             
    return beans.MenuItems(
        *menu_options            
    )


def modify(action, path_param=None):    
    """ Function to move movies to location specified in "destiny_conf_dir"
    argument. Movies(absolute paths) are given in URL param.
    """
    reload = True
    
    for k, item in request.args.items(True):
        src = item
        if action == 'move':
            dest = join(app.config[path_param], os.path.split(item)[-1])                            
            shutil.move(src, dest)
            
        elif action == 'delete':
            shutil.rmtree(src)  
            
        elif action == 'refresh':
            
            reload = False
            task_url = '/files/feed_movie?path=%s&action=refresh' % item
            Task(task_url).commit()                       
        
    if reload:
        return beans.Composite(
            beans.Reload(slot = 'LEFT'),
            beans.Reload(slot = 'CONTENT'),
        )
    return beans.MultiLoader()    

    
@files.route('/files/move_watched', methods=['GET', 'POST'])
@common.jsonify
def move_watched():
    return modify(action='move', path_param='MOVIES_WATCHED_DIR')

    
@files.route('/files/move_ready', methods=['GET', 'POST'])
@common.jsonify
def move_ready():
    return modify(action='move', path_param='MOVIES_READY_DIR')


@files.route('/files/delete', methods=['GET', 'POST'])
@common.jsonify
def delete():
    return modify(action='delete')        


@files.route('/files/refresh', methods=['GET', 'POST'])
@common.jsonify
def refresh():
    app.logger.debug('refreshing')
    return modify(action='refresh')