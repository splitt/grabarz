## -*- coding: utf-8 -*-
from flask import Module, session
from grabarz.lib.beans import (Config, Desktop, MultiLoader, HTML, Menu, 
                               Actions, Composite, Window, TimerRegister, 
                               Infobox)
from grabarz.lib.utils import jsonify, fixkeys
from grabarz import app

layout = Module(__name__)

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
                 url="/layout/content",
             ),
        ]
    )
    
@layout.route('/layout/top')
@jsonify
def top():
    return HTML(
        content = "<img src='/static/_logo.png' alt='logo'/>",
    )

@layout.route('/layout/content')
@jsonify
def content():
    return HTML(
        heading=None,
        content="sparta!!! " * 1000,
        scroll="NONE",
    )

@layout.route('/layout/left')
@jsonify
def left():
    
    return Menu(
        sections = ["Filmy", "Seriale", "System"],
        
        Filmy = [
                 
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'gotowe',              
                 icon = "icon-eye",   
            ),
            
                             
            dict(
                 url = '/movies/add',
                 slot = 'internal',
                 id = 'aaa',
                 title = 'dodaj',              
                 icon = "icon-add",   
            ),
                                 
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'oczekujące na akceptację',
                 icon = "icon-clock_red",                     
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'obejrzane',
                 icon = "icon-television_delete",      
                           
            ),
            
            dict(
                 url = '/',
                 slot = 'CONTENT',
                 id = 'aaa',
                 title = 'ustawienia',
                 icon = "icon-film_edit",  
                      
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
                 url = '/',
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
    session['messages'] = []
    
    return TimerRegister(
        name = 'messages',
        action = '/layout/messages',
        interval =  3000,
        slot = 'internal',
                        
    )



@layout.route('/layout/messages')
@jsonify
def messages():
    rv =  Composite(
        *[Infobox(
            title = info[0],
            text = info[1],
            duration = 5000,
            ) for info in session['messages']]                     
    )
    session['messages'] = []
    return rv