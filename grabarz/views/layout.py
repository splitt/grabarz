## -*- coding: utf-8 -*-
import os
from flask import Module, session, g, request
from grabarz import app, models
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Actions, Composite, Window, TimerRegister, 
                               Infobox, Slots, Reload)
from grabarz.lib.utils import jsonify, fixkeys


layout = Module(__name__)

GIGABYTE = 1024 * 1024 * 1024


@layout.route('/layout/test')
@jsonify
def test():
    from datetime import datetime
    app.logger.debug('%s TASK TEST' % str(datetime.now()))
    return ''
    

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
    return Slots(
             dict(
                 id='TOP',
                 split=True,
                 data=['NORTH', 60],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/layout/top",
             ),               
               
             dict(
                 id='LEFT',
                 split=True,
                 data=['WEST', 200],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/layout/left",
             ),

             dict(
                 id='CONTENT',
                 split=True,
                 data=['CENTER', 100, 100, 100],
                 margins=[5, 5, 5, 5],
                 scroll='AUTO',
                 url="/movies/ready_to_watch",
             ),         
        )
    
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
                 data=['NORTH', 60],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/layout/top",
             ),               
               
             dict(
                 id='LEFT',
                 split=True,
                 data=['WEST', 200],
                 margins=[5, 5, 5, 5],
                 scroll='NONE',
                 url="/layout/left",
             ),

             dict(
                 id='CONTENT',
                 split=True,
                 data=['CENTER', 100, 100, 100],
                 margins=[5, 5, 5, 5],
                 scroll='AUTO',
                 url="/movies/ready_to_watch",
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

    
    return HTML(
        content = (
           "<img src='/static/_logo.png' alt='logo'/>" +
           "<span class='discStats'>" +
           "<span >Dane zajmują: <b>%.2f GB</b></span><br/>" % used +
           "<span >Pozostało wolnych: <b>%.2f GB</b></span>" % available +
           "</span>" 
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


@layout.route('/layout/left')
@jsonify
def left():
    gfc = lambda x: get_folder_count(app.config[x])
    
    return Menu(
        sections = ["Filmy", "Seriale", "System"],        
        
        Filmy = [
            
            dict(
                 url = '/movies/add',
                 slot = 'internal',
                 id = 'movies-add',
                 title = 'dodaj',              
                 icon = "icon-add",   
            ),
                             
            dict(
                 url = '/movies/ready_to_watch',
                 slot = 'CONTENT',
                 id = 'movies-ready_to_watch',
                 title = 'gotowe [%s]' % gfc('MOVIES_READY_DIR'),              
                 icon = "icon-eye",
            ),
                                        
            
            dict(
                 url = '/movies/downloading',
                 slot = 'CONTENT',
                 id = 'movies-downloading',
                 title = 'Ściągane [%s]' % gfc('MOVIES_DOWNLOADING_DIR'),         
                 icon = "icon-arrow_down",   
            ),            
                                 
            dict(
                 url = '/movies/found',
                 slot = 'CONTENT',
                 id = 'movies-founded',
                 title = 'znalezione [%s]' % gfc('MOVIES_FOUND_DIR'),
                 icon = 'icon-zoom',                     
            ),
            
            dict(
                 url = '/movies/watched',
                 slot = 'CONTENT',
                 id = 'movies-watched',
                 title = 'obejrzane [%s]' % gfc('MOVIES_WATCHED_DIR'),
                 icon = "icon-television_delete",      
                           
            ),
            
            dict(
                 url = '/movies/settings',
                 slot = 'CONTENT',
                 id = 'movies-settings',
                 title = 'ustawienia',
                 icon = "icon-film_edit",  
                      
            ),        
            
            dict(
                 url = '/movies/test',
                 slot = 'CONTENT',
                 id = 'movies-test',
                 title = 'test',                      
            ),  
        ],               
        
        Seriale = [
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'dodaj',              
                 icon = "icon-film_add",   
            ),
                                 
            dict(
                 url = '/movies/ready_to_watch',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'gotowe',              
                 icon = "icon-film_go",   
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'oczekujące na akceptację',
                 icon = "icon-film_key",                     
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'obejrzane',
                 icon = "icon-film_save",      
                           
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'ustawienia',
                 icon = "icon-film_edit",  
                      
            ),                                 
        ],          
        
        System = [
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'rtorrent',              
                 icon = "icon-application_double",   
            ),
                                 
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'procesy',              
                 icon = "icon-cog",   
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'cron',
                 icon = "icon-clock_link",                     
            ),                               
        ],               
                     
    )    
    
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
