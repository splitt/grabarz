## -*- coding: utf-8 -*-
from __future__ import with_statement

import time, re, os, shutil, ConfigParser
from datetime import date
from copy import deepcopy
from os.path import join, split

import mechanize
from imdb import IMDb
from flask import Module, request
from pyquery import PyQuery as pq

from grabarz import app, common
from grabarz.lib import beans, utils, torrent

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
    
    ('move_completed', beans.MenuItem(
                        label = "przenieś do gotowych",
                        icon = "icon-eye",
                        link = dict(
                            url = "/files/move_completed%s",
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

MENU_OPTIONS_MAP = dict(
    completed = ['refresh', 'delete', 'separator','move_watched'],
    downloading = ['refresh','separator', 'delete'],
    uploading = ['refresh','separator', 'delete'],
    found = ['refresh', 'start_downloading', 'separator','delete'],
    queued = ['refresh', 'start_downloading', 'separator','delete'],
    watched = ['refresh', 'separator', 'move_completed', 'delete'],           
)

    
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


def title_year_from_filename(filename):
    """ Parse title and production year from given filename"""
    year_re = '(1|2)[0-9]{3}$'
    
    title = filename.replace('.', ' ')
    title = re.sub('(1080|720).*$', '', title).strip()
    title = re.sub('\(|\)|\[|\]', '', title).strip()
    
    year =  re.search(year_re, title) 
    if year:
        year = year.group()   
    title = re.sub(year_re, '', title).strip().capitalize()
        
    return title, year
    
    
def get_cover_from_google(title):
    """ Search in google docs cover """
                

@files.route('/files/feed-movie-process')
@common.jsonify
def feed_movie():
    """Creates folder with movie data."""
    import pdb;pdb.set_trace()
    hlog = common.HydraLog(slot = `time.time()`, heading = "Analiza '%s'")
    data = dict(MOVIE_DATA)

    #: adding new torrent
    if request.form.get('torrent_url'):
        torrent_data = torrent.get_torrent_data(request.form['torrent_url'])
        path = join(app.config['RTORRENT_DOWNLOADING_DIR'], 
                    torrent_data['info']['name']) 
        filename = sorted(torrent_data['info']['files'], 
                          key = lambda x: x['length'])[-1]['path'][-1]                                    
        title, year = title_year_from_filename(filename)        
        
        hlog.emit(u'Sparsowano tytuł filmu: "%s" na podstawie pliki' % title)        
        if year:
            hlog.emit(u'Wyciągnięto rok produkcji filmu:%s ' % year)      
    
    #: refreshing dat - getting info from ini_file    
    else:
        path = request.args['path']
        title = path.split('/')[-1]
        cfg = ConfigParser.RawConfigParser()        
        cfg.read(join(path, 'grabarz.ini'))
        ini_data = dict(cfg.items('data'))
        year = ini_data.get('year')
        title = ini_data.get('title')            
        hlog.emit(u'Rozpoczynam odświeżanie "%s" ' % title)
                                        
    #: Searching in IMDB database    
    hlog.emit(u'Szukam filmu w bazie IMDB...')    
    try:
        movie = imdb.search_movie(title)[0]
    except IndexError:
        hlog.emit(u'[ERROR] Nie rozpoznano filmu w bazie IMDB')
        return 'ERROR'        
    imdb_id = movie.getID()
    imdb_data = imdb.get_movie(imdb_id)
    title = data['title'] = imdb_data['title']
    if not all(imdb_data['rating'], imdb_data['year'],imdb_data['runtime']):
        hlog.emit(u'[ERROR] Nie można znaleść poprawnego filmu w bazie IMDB')
        return 'ERROR'        
    hlog.emit(u'Znaleziono film w bazie IMDB')
    
    #: feeding from IMDB    
    data['imdb_rating'] = imdb_data.get('rating')
    data['runtime'] =  ' '.join(imdb_data.get('runtime')[:1])
    data['year'] =  imdb_data.get('year')
    data['genres'] = ' '.join(imdb_data.get('genres'))
    data['date_added'] = '-'.join(str(date.today()).split('-')[::-1])
                
    #: Saving cover url
    cover_url = imdb_data.get('cover url') or get_cover_from_google(title)  
    utils.download(cover_url, join(path, 'cover.jpg'))        
                     
    #: Searching in Filmweb site
    hlog.emit(u'Szukam definicji w bazie Filmweb')
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
        hlog.emit(u'Znaleziono film "%s" w bazie Filmweb' % title)
        d = pq(resp.read())
        data['filmweb_rating'] = d('.rating .average').text().replace(',', '.')
        data['description'] = d('.filmDescrBg').text()
        data['filmweb_url'] = br.geturl()
        data['polish_title'] = d('.fn').text()
        data['filmweb_opinions'] = '\n'.join(d('.fltTitle')
                                        .text().split('czytaj dalej'))
    else:
        app.logger.warning(u'Nie znaleziono filmu "%s" w bazie Filmweb' % title)    
        
    data['__space__'] = "&nbsp;" * 8
    hlog.emit(u"""
        =================================<br/>
        Podstawowe informację o filmie:<br/> 
        %(__space__)srating IMDB: %(imdb_rating)s<br/>
        %(__space__)sFilmweb: %(filmweb_rating)s<br/>
        %(__space__)sPolski tytuł: "%(polish_title)s"<br/>
        %(__space__)srok produkcji: %(year)s<br/>                       
    """% data) 
            
    if request.form.get('torrent_url'):
        #:-- new torrent succesfully recognizes ad film or tvshow --
        
        #: saving torrent file    
        utils.download(request.form.get('torrent_url'), 
                       app.config['RTORRENT_WATCH_DIR'])
        
        #: making link to movies directory
        os.symlink(path, join(app.config['MOVIES_DOWNLOADING_DIR']))     
        hlog.close()
    else:
        common.reload_slot('@center', method = 'sql')
        
    #: Dumps data to ini file
    config = ConfigParser.RawConfigParser()    
    config.add_section('data')
    for k, v in data.items():
        val = unicode(v).encode('utf-8')
        config.set('data', k, val)
                
    with open(join(path, 'grabarz.ini'), 'wb') as configfile:
        config.write(configfile)
        
    hlog.emit(u'Uaktualniono plik ini<br/><br/>KONIEC')            
    hlog.close()
    return 'OK'        
    

def get_torrent_info(init_data, path):
    return dict(
        name="name",
        status="status",
        size="size",
        dl="dl",
        ul="ul",
        ratio="ratio",
        eta="eta",
        seed_peers="seed_peers",
        priority="priority",           
        __params__  = dict(
            style = 'movie_row',
#            uid = path,
        )        
    )
    
    
def get_expander_info(init_data, path):

    ratings = '%s Imdb: <b>%s</b></span></br>' % (IMDB_ICO, 
                                                  init_data['imdb_rating'])
    
    imdb_rating = average = float(init_data['imdb_rating'])
    
    if init_data.get('filmweb_rating'):
        ratings += (
            '<a target="_blank" href="%s">' % init_data['filmweb_url'] +
            '<span> %s Filmweb:&nbsp;' % FILMWEB_ICO +
            '<b>%s</b></span></a></br>' % init_data['filmweb_rating'] 
        )
                        
        filmweb_rating = float(init_data.get('filmweb_rating'))                         
        average = str((imdb_rating + filmweb_rating) / 2)
                    
    ratings = (
        '<!--%s-->' % average + 
        u'<span class="average"> Średnia: %s</span></br></br>' % average +
        ratings
    )            
         
    desc = '<br/>'.join([
        u"<span class='title'>%s (%s)</span>" % \
            (init_data['title'], init_data.get('polish_title') or ''), 
        '<b>Rok produkcji:</b> %s ' % init_data['year'],
        '<b>Czas:</b> %s minut '% init_data['runtime'],
        '<b>Gatunki</b> %s' % init_data['genres'],            
        (init_data.get('description') or '')[:700],            
    ])    
    cover = '<img src="%s"/>' % join('_MOVIES_DIR',split(path)[-1],
                                     init_data['title'],
                                     'cover.jpg')
    html = "<table class='row_expander'><tr>%s</tr></table>"
    cells = ''.join("<td class='%s'>%s</td>" % (c, s) 
                    for c, s in zip(['cover','ratings', 'desc'], 
                                    [cover,ratings, desc]))
    return html % cells
            
    
@files.route('/files/files_listing')
@common.jsonify
def files_listing():
    """ Listing files for given type and filter in filesystem """    
    filter = request.args['filter']
    type = request.args['type']
    title = request.args.get('title') 
    
    dirs = []
    menu_options = []
    
    if filter in ['movies', 'all']:
        if type == 'all':
            menu_options = []
            dirs.extend([
                'MOVIES_COMPLETED_DIR', 'MOVIES_WATCHED_DIR',
                'MOVIES_DOWNLOADING_DIR','MOVIES_FOUND_DIR',
            ])
        else:
            menu_options = MENU_OPTIONS_MAP[type]
            dirs.append('MOVIES_%s_DIR' % type.upper())
                                      
    data = []
    paths = [app.config[dir] for dir in dirs]        
    config = ConfigParser.RawConfigParser()
    
    for path in paths:
        #: Extract data from ini files
        for dir in os.listdir(path):                            
            dir_path = join(path, dir) 
            config.read(join(dir_path, 'grabarz.ini'))
            ini_data = dict(config.items('data'))            
            ini_data = dict( (k, v.decode('utf-8')) for k, v in ini_data.items())
            
            row = get_torrent_info(ini_data, path)
            row['expander'] = get_expander_info(ini_data, path)
            row['__expander__'] = 'false'
                                    
            data.append(row)
                            
    return beans.Composite(
#        beans.HackScriptButton(
#            script = """
#                $('.x-tool-down').click();                
#                $('.x-grid3-row-expander').click();
#                                                    
#            """,
#            label = 'Rozwiń',            
#        ),
        beans.Listing(
             heading = title,
#             paging = True,
#             paging_url = '/aaaaaaaaa',         
             menu_url = '/files/get_context_menu?items=%s' % ','.join(menu_options),
             autoexpand_column = "title",
             param_name = 'uid',
             columns=[
                dict(
                     renderer = 'expander',
                     expander='{expander}',
                ),                  
                dict(
                     renderer = 'numberer',
                ),
                dict(
                     renderer = 'checkbox',                 
                ),
                dict(
                     width="300",
                     title="Name",
                     id="name",
                ),
                dict(
                     width="100",
                     title="Status",
                     id="status",
                ),
                dict(
                     width="100",
                     title="Size",
                     id="size",
                ),
                dict(
                     width="100",
                     title="DL",
                     id="dl",
                ),
                dict(
                     width="100",
                     title="Ul",
                     id="ul",
                ),
                dict(
                     width="100",
                     title="Ratio",
                     id="ratio",
                ),
                dict(
                     width="100",
                     title="ETA",
                     id="eta",
                ),
                dict(
                     width="100",
                     title="seed_peers",
                     id="seed_peers",
                ),  
                dict(
                     width="100",
                     title="Priority",
                     id="priority",
                ),               
                
    #            dict(
    #                 width="100",
    #                 title="Plakat",
    #                 id="cover",
    #            ),                   
    #            dict(
    #                 width="500",
    #                 title="Tytuł",
    #                 id="title",
    #                 sortable = "true",
    #            ),
    #            dict(
    #                 width="100",
    #                 title="Oceny",
    #                 id="ratings",
    #                 sortable = "true",
    #            ),                  
    #            dict(
    #                 width="60",
    #                 title="Data dodania",
    #                 id="date_added",
    #                 sortable = "true",
    #            ),
            ],
            data=data,
    ))


            

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
                option['link']['url'] = option['link']['url'] % utils.post2get()
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
            task_url = '/files/feed-movie-process?path=%s&action=refresh' % item
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

    
@files.route('/files/move_completed', methods=['GET', 'POST'])
@common.jsonify
def move_completed():
    return modify(action='move', path_param='MOVIES_COMPLETED_DIR')


@files.route('/files/delete', methods=['GET', 'POST'])
@common.jsonify
def delete():
    return modify(action='delete')        


@files.route('/files/refresh', methods=['GET', 'POST'])
@common.jsonify
def refresh():
    app.logger.debug('refreshing')
    return modify(action='refresh')