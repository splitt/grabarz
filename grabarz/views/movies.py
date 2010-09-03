## -*- coding: utf-8 -*-
from os.path import join

from flask import Module, request

from grabarz import app
from grabarz.lib import torrent, tasks
from grabarz.lib.utils import jsonify
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Window, Form, Button, Link, CharField, Infobox)


movies = Module(__name__)


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

from celery.decorators import task

@task
def test(x, y):
    return x + y    
    
@movies.route('/movies/process', methods=['GET', 'POST'])
@jsonify
def process():
    """ Reads information from torrent file and creates grabarz.ini 
    file for given movie."""
    
    
    
    import pdb;pdb.set_trace()    

    file = torrent.get_torrent_filenames(request.form['torrent_src'])[0]
        
    destiny_dir = join(app.config['DUMP_DIR'], 'movies')
    tasks.create_data_files(file, destiny_dir)    
    
    print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        
    return Infobox(                             
        text = 'Rozpoczęto pobiernia filmu %s file' % file,
    )