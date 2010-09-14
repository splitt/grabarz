## -*- coding: utf-8 -*-
from __future__ import with_statement

import re
import os
import shutil
from os.path import join, split
import ConfigParser
from copy import deepcopy
from datetime import date
from pprint import pformat

import mechanize
from pyquery import PyQuery as pq
from flask import Module, request, session, g, redirect

from grabarz import app
from grabarz.lib import torrent
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Listing, Window, Form, Button, Link, CharField,
                               Infobox, MenuItems, MenuItem, Reload,Composite)
from grabarz.lib.utils import jsonify, post2get, download, HydraLog
from grabarz.cron import Task

from imdb import IMDb
imdb = IMDb()
movies = Module(__name__)
IMDB_ICO = '<img src="/static/_imdb.png">'
FILMWEB_ICO = '<img src="/static/_filmweb.ico">'

MENU_OPTIONS = [
    ('refresh', MenuItem(
                    label = "odśwież dane",
                    icon = "icon-arrow_refresh",
                    link = dict(
                        url = "/movies/refresh%s",
                        slot = "CONTENT",               
                    ),
                ),
    ),
    
    ('start_downloading', MenuItem(
                            label = "Zacznij pobieranie",
                            icon = "icon-television_delete",
                            link = dict(
                                url = "/movies/move_watched%s",
                                slot = "CONTENT",               
                            )
                        ),
    ),    
    
    ('move_watched', MenuItem(
                        label = "przenieś do obejrzanych",
                        icon = "icon-arrow_down",
                        link = dict(
                            url = "/movies/move_watched%s",
                            slot = "CONTENT",               
                        )
                    ),
    ),
    
    ('move_ready', MenuItem(
                        label = "przenieś do gotowych",
                        icon = "icon-eye",
                        link = dict(
                            url = "/movies/move_ready%s",
                            slot = "CONTENT",               
                        )
                    ),
    ),
    
    ('separator', dict(type = 'separator')),
        
    ('delete', MenuItem(
                    label = "Usuń z dysku",
                    icon = "icon-delete",
                    link = dict(
                        url = "/movies/delete%s",
                        slot = "CONTENT",               
                    )
                ),
    ),            
]


@movies.route('/movies/feed_movie')
def feed_movie(absolute_path = None):
    """Creates folder with movie data.
    
    @param absolute_path: absolute path where function will drop data files.
    @param report_slot: slot's it holding log.
    @param type:  
    """
    absolute_path = absolute_path or request.args.get('uid')
    type = request.args.get('type') or 'new'
    
    folder = split(absolute_path)[-1] 
    data = {}    
    hydra_log = HydraLog('feed_movie|'+folder)
            
    #: Parsing movie filename for proper title            
    if type == 'new':
        year_re = '(1|2)[0-9]{3}$'
        name = folder.replace('.', ' ')
        name = re.sub('(1080p|720p).*$', '', name).strip()        
        title = re.sub('(1|2)[0-9]{3}$', '', name).strip().capitalize()
        movie_year = re.search(year_re, name)
    elif type == 'refresh':
        config = ConfigParser.RawConfigParser()        
        config.read(join(absolute_path, 'grabarz.ini'))
        ini_data = dict(config.items('data'))
        movie_year = ini_data.get('year')
        title = ini_data.get('title')
            
    config = ConfigParser.RawConfigParser()
                            
    #: Searching in IMDB database
    hydra_log.emit(u'Rozpoczynam procesowanie filmu "%s" ' % title)    
    try:
        movie = imdb.search_movie(title)[0]
    except IndexError:
        app.logger.debug(u'Nie rozpoznano filmu "%s" w bazie IMDB' % title)
#        set_flash(u'Nie rozpoznano filmu %s' % title)
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

    data['imdb_rating'] = imdb_data['rating']
    data['runtime'] =  ' '.join(imdb_data['runtime'][:1])
    data['year'] =  imdb_data['year']
    data['genres'] = ' '.join(imdb_data['genres'])
    data['date_added'] = '-'.join(str(date.today()).split('-')[::-1])
    
    #: Saving cover url
    if imdb_data.get('cover url'):    
        download(imdb_data['cover url'], join(full_work_dir, 'cover.jpg'))
                     
    #: Searching in Filmweb site
    br = mechanize.Browser()
    resp = br.open('http://www.filmweb.pl/search?q=%s' % title.replace(' ','+'))
    
    #: Dodge commercial Welcome :)
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
        
        
    hydra_log.emit(u'Tworzę plik ini na podstawie znalezionych ' + 
                      'informaci:\n %s' % pformat(dict((k,`v`[:60]) 
                                                       for k,v in data.items()))
                     )
    
    #: Dumps data to ini file    
    config.add_section('data')
    for k, v in data.items():
        val = unicode(v).encode('utf-8')
        config.set('data', k, val)
        
    with open(join(full_work_dir, 'grabarz.ini'), 'wb') as configfile:
        config.write(configfile)
        

@movies.route('/movies/add')
@jsonify
def add():
    """ Window for entering torrent file link """
    
    return Window(                
        slotname = '/movies/add',
        heading = 'Dodanie torrenta filmowego',
        height = 130,
        object = Form(
            slotname = '/movies/add',            
            buttons = [
                Button(
                     slot = "content",
                     link = Link(
                        url = "/movies/process",
                        slot = "window_add_entry",
                     ),
                     label = "Dodaj"
                ),
            ],    
            formdefs = [
                CharField(
                    name='torrent_src',
                    label='Podaj adres pliku torrent',
                    width=350,
                 ),                      
            ],            
        ),
    )


def get_movies_list(title, path, menu_options):
    """ Listing movies for given path in filesystem """
    
    session['current_page'] = request.path
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
                
    return Listing(
         heading=title,
         sid='movies-ready_to_watch',
         paging = False,         
         menu_url = '/movies/get_context_menu?items=%s' % menu_options,
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
    )


@movies.route('/movies/ready_to_watch')
@jsonify
def ready_to_watch():
    """ Displays list of downloaded movies """
    return get_movies_list(title = "Filmy gotowe do obejrzenia",
                           path = app.config['MOVIES_READY_DIR'],
                           menu_options = ['refresh', 'delete', 
                                           'separator','move_watched'])


@movies.route('/movies/downloading')
@jsonify
def downloading():
    """ Displays list of current downloading movies """
    return get_movies_list(title = "Filmy aktualnie ściągane",
                           path = app.config['MOVIES_DOWNLOADING_DIR'],
                           menu_options = ['refresh','separator', 'delete'])
    

@movies.route('/movies/found')
@jsonify
def founded():
    """ Displays list of founded movies by robots """
    return get_movies_list(title = "Filmy znalezione przez Grabarza",
                           path = app.config['MOVIES_FOUND_DIR'],
                           menu_options = ['refresh', 'start_downloading', 
                                           'separator','delete',]
                           )
    
    
@movies.route('/movies/watched')
@jsonify
def watched():
    """ Displays list of watched movies """
    return get_movies_list(title = "Filmy obejrzane",
                           path = app.config['MOVIES_WATCHED_DIR'],
                           menu_options = ['refresh', 'separator', 
                                           'move_ready', 'delete'])    
    
        
@movies.route('/movies/process', methods=['GET', 'POST'])
@jsonify
def process():
    """ Reads information from torrent file and creates grabarz.ini 
    file for given movie."""
    
    file = torrent.get_torrent_filenames(request.form['torrent_src'])[0]
        
    destiny_dir = join(app.config['DUMP_DIR'], 'movies')
    tasks.create_data_files(file, destiny_dir)
            
    return Infobox(                             
        text = 'Rozpoczęto pobiernia filmu %s file' % file,
    )
    

@movies.route('/movies/get_context_menu', methods=['GET', 'POST'])
@jsonify    
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
             
    return MenuItems(
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
            args = request.environ['QUERY_STRING']
#            Task('/movies/feed_movie?%s' % args, 0).cronify()                       
        
    if reload:
        return Composite(
            Reload(slot = 'LEFT'),
            Reload(slot = 'CONTENT'),
        )
    return MultiLoader()    
    
@movies.route('/movies/move_watched', methods=['GET', 'POST'])
@jsonify    
def move_watched():
    return modify(action='move', path_param='MOVIES_WATCHED_DIR')

    
@movies.route('/movies/move_ready', methods=['GET', 'POST'])
@jsonify    
def move_ready():
    return modify(action='move', path_param='MOVIES_READY_DIR')


@movies.route('/movies/delete', methods=['GET', 'POST'])
@jsonify    
def delete():
    return modify(action='delete')        


@movies.route('/movies/refresh', methods=['GET', 'POST'])
@jsonify    
def refresh():
    app.logger.debug('refreshing')
    return modify(action='refresh')