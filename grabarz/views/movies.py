## -*- coding: utf-8 -*-
from __future__ import with_statement

import os
from os.path import join
import ConfigParser

from flask import Module, request

from grabarz import app
from grabarz.lib import torrent, tasks
from grabarz.lib.utils import jsonify
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Listing, Window, Form, Button, Link, CharField,
                               Infobox)

movies = Module(__name__)
IMDB_ICO = '<img src="/static/_imdb.png">'
FILMWEB_ICO = '<img src="/static/_filmweb.ico">'

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


@movies.route('/movies/ready_to_watch')
@jsonify
def ready_to_watch():
    """ Displays list of downloaded movies """
    
    data = []
    config = ConfigParser.RawConfigParser()
    
    #: Extract data from ini files
    for i, dir in enumerate( os.listdir(app.config['MOVIES_DIR'])):
        if i == 0:
            continue
                            
        dir_path = join(app.config['MOVIES_DIR'], dir) 
        config.read(join(dir_path, 'grabarz.ini'))
        d = dict(config.items('data'))
        
        d = dict( (k, v.decode('utf-8')) for k, v in d.items())
        ratings = '%s Imdb: <b>%s</b></span></br>' % (IMDB_ICO, d['imdb_rating'])
        
        if d.get('filmweb_rating'):
            ratings += u''.join([
                '<a target="_blank" href="%s">' % d['filmweb_url'],
                '<span> %s Filmweb:' % FILMWEB_ICO,
                '<b>%s</b></span></a></br>' % d['filmweb_rating'] 
            ])
            
            average = str((float(d['imdb_rating']) + 
                           float(d['filmweb_rating']))/2)
                        
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
            d['description'][:800],
            d['genres'],
        ])
        
        d['cover'] = '<img src="%s"/>' % join('_MOVIES_DIR',dir, 'cover.jpg')
        d['__params__'] = dict(
            style = 'movie_row'
            )    
        data.append(d)
                    
    
    return Listing(
         heading="Filmy gotowe do obejrzenia",
         sid='movies-ready_to_watch',
         paging = False,         
         autoexpand_column = "title",
         columns=[
            dict(
                 renderer = 'numberer',
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
        ],
        data=data,
    )

    
    
    
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