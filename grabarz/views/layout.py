## -*- coding: utf-8 -*-
import os
from flask import Module, session, g, request
from grabarz import app, models
from grabarz.lib import beans
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Actions, Composite, Window, TimerRegister, 
                               Infobox, Slots, Reload)
from grabarz.lib.utils import jsonify, fixkeys


layout = Module(__name__)

GIGABYTE = 1024 * 1024 * 1024


@layout.route('/layout/config')
@jsonify
def config():
    return Config(
        title="grabarz",
        default_errorwindowtitle="Wystąpił błąd aplikacji",
        debug=app.config['DEBUG'],
        theme="olive",
        history_enabled=True,
    )

@layout.route('/layout/slots')
@jsonify
def slots():    
    return Desktop(
        heading='',
        menu_items=[
            dict(
                label='Wyloguj',
                icon='icon-door_out',
                link=dict(
                    url='/auth/logout',
                    slot='dashboard',
                )
            ),
        ],
        show_desktop_tool=True,
        show_group_windows_tool=True,
        icon='icon-user',
        button_label='Menu',

        slots=[
             dict(
                 id='TOP',
                 split=True,
                 data=['NORTH', 120],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/layout/top",
             ),  
        ]
    )
    
@layout.route('/layout/top')
@jsonify
def top():
    
    #: Counting disk stats
    disk = os.statvfs("/")
    available = float(disk.f_bsize * disk.f_bavail) / GIGABYTE
    used = disk.f_bsize * (disk.f_blocks - disk.f_bavail) / GIGABYTE
    
    
    return beans.Composite(                   
        beans.HTML(
            content = (
               "<img src='/static/_logo.png' alt='logo'/>" +
               "<span class='discStats'>" +
               "<span >Dane zajmują: <b>%.2f GB</b></span><br/>" % used +
               "<span >Pozostało wolnych: <b>%.2f GB</b></span>" % available +
               "</span>" 
            )
        ),
        
        beans.Actions(
            links = [
                beans.MenuButton(
                    icon = 'icon-add',
                    type = 'button',
                    title = 'Dodaj torrent',
                    link = beans.Link(
                        url = '/system/window-torrent-add',
                        slot = 'internal',                                
                    ),
                ),
                beans.MenuSeparator(),
                beans.MenuButton(
                    icon = 'icon-film',
                    title = 'Filmy',
                    link = beans.Link(
                        url = '/movies/window-movies',
                        slot = 'internal',                                
                    ),
                ),
                beans.MenuButton(
                    icon = 'icon-film_link',
                    title = 'Seriale',
                    link = beans.Link(
                        url = '',
                        slot = 'internal',                                
                    ),
                ),
                beans.MenuSeparator(),
                beans.MenuButton(
                    icon = 'icon-cog',
                    title = 'Procesy',
                    link = beans.Link(
                        url = '',
                        slot = 'internal',                                
                    ),
                ),
            ]                      
        )        
    ) 
    


@layout.route('/layout/content')
@jsonify
def content():
    return HTML(
        heading=None,
        content="sparta!!! " * 1000,
        scroll="NONE",
    )


def get_folder_count(path):
    """ Returns count of movies in given path """
    return str(len(os.listdir(path)))


@layout.route('/layout/rtorrent')
@jsonify
@fixkeys
def rtorrent():
    return Window(
     external_url = '/layout/content',
     slotname = 'window-rtorrent',
     heading = 'rtorrent',
     width = 800,
     height = 600,  
    )
    
@layout.route('/layout/init')
@jsonify
def init():    
    
    return TimerRegister(
        name = 'messages',
        action = '/layout/updates',
        interval =  app.config['UPDATE_INTERVAL'],
        slot = 'internal',                        
    )


@layout.route('/layout/updates')
@jsonify
def updates():    
    beans = models.CallbackUpdate.dump()
    
    return Composite(*beans)
