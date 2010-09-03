## -*- coding: utf-8 -*-
from flask import Module, request

from grabarz import app
from grabarz.lib import torrent
from grabarz.lib.utils import jsonify
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Window, Form, Button, Link, CharField, Infobox)


movies = Module(__name__)


@movies.route('/movies/add')
@jsonify
def add():
    """ Window for entering torrent file link"""
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
    
    
@movies.route('/movies/process', methods=['GET', 'POST'])
@jsonify
def process():
    """ Reads information from torrent file and creates grabarz.ini 
    file for given movie."""    

    files = torrent.get_torrent_filenames(request.form['torrent_src'])
    
    return Infobox(                
        text = 'Torrent z plikami : %s przekazany do rTorrenta' % ''.join(files)
    )