## -*- coding: utf-8 -*-
import os
from flask import Module, request, session
from grabarz import app, common
from grabarz.lib import beans

layout = Module(__name__)
GIGABYTE = 1024 * 1024 * 1024
    

def icon_factory(ico = 'icon-arrow_down'):
    return """
        <span style="width: 16px; height: 16px; display: inline;" 
            class="%s clickable-icon ">&nbsp;&nbsp;&nbsp;&nbsp;
        </span>
    """ % ico


def get_folder_count(path):
    """ Returns count of movies in given path """
    return str(len(os.listdir(path)))



@layout.route('/layout/config')
@common.jsonify
def config():
    session['callback_updates'] = []
    
    return beans.Config(
        title="grabarz",
        default_errorwindowtitle="Wystąpił błąd aplikacji",
        debug=app.config['DEBUG'],
        theme="olive", #slate
        history_enabled=True,
    )
    

@layout.route('/layout/slots')
@common.jsonify
def slots():
    return beans.Slots(
        dict(
            id='top',
            data=['NORTH', 20],
            margins=[5, 5, 5, 5],
            scroll='NONE',            
            link = beans.Link(
                url="/layout/top",
            )
        ),          
        
        dict(
            id='left',
            heading = "Filter",
            collapsible = True,
            data=['WEST', 140],
            margins=[10, 0, 0, 5],
            scroll='NONE',
            link = beans.Link(
                url="/layout/left",
            )
        ),
        
        dict(
            id='@center',
            split=True,
            data=['CENTER', 220],
            margins=[5, 5, 0, 5],
            scroll='NONE',
            link = beans.Link(
                url="/layout/@center",
            )
        ),
        
        dict(
            id='bottom',
            split=True,
            data=['SOUTH', 20],
            margins=[5, 5, 5, 5],
            scroll='NONE',
            link = beans.Link(
                url="/layout/bottom",
            )            
        ),     
        
    )

    
@layout.route('/layout/top')
@common.jsonify
def top():
    return beans.Actions(
        links = [
            beans.MenuButton(
                icon = 'icon-add',
                type = 'button',
                title = 'Add torrent',
                link = beans.Link(
                    url = '/system/window-torrent-add',                                
                ),
            ),

            beans.MenuButton(
                icon = 'icon-cog',
                title = 'Process',
                link = beans.Link(),
            ),
            beans.MenuSeparator(),
                            
            beans.MenuButton(
                icon = 'icon-wand',
                title = 'Settings',
                link = beans.Link(),
            ),
            beans.MenuButton(
                icon = 'icon-question',
                title = 'About',
                link = beans.Link(
                    url = '/calendar/calendar_window'
                ),
            ),                                                
        ]                      
    )
        

@layout.route('/layout/left')
@common.jsonify
def left():
    return beans.Composite(        
        beans.Form(
            formdefs = [
                beans.CheckBoxField(
                    name='movies',
                    label='Movies',
                 ),
                beans.CheckBoxField(
                    name='shovs',
                    label='Tv shows',
                 ),             
            ],     
            buttons = [
                beans.Button(
                    label = 'apply',
                    link = beans.Link()                                    
                )
                       
            ]           
        ),
        
        beans.HTML(
            content = """
            <div class="x-small-editor x-panel-header x-component">
                <span  class="x-panel-header-text">Menu </span>
            </div>""",                   
        ),
                                   
        beans.Tree(
            heading = None,
            sid = "menu",
            url = "/layout/left-data",        
            autoexpand_column =  "id",
            expand = False,
            columns = [
                beans.Column(
                    renderer = 'treegridcell',
                    title = "Pliki",
                    id = "id",
                    width = '100',                    
                ),   
                                   
                beans.Column(
                    renderer = 'icon',
                    title = "",
                    id = "ico",
                    width = '40',
                ),
                                   
            ],                    
        ),
        
    
    )
    
    
@layout.route('/layout/left-data', methods=['GET', 'POST'])
@common.jsonify
def left_data():
    return beans.Data(
                      
        #:--- Downloading ---
        dict(             
            id = '--All files--',
            
            ico = dict(
                url = "/system/listing",
                slot = 'internal', 
                icon = 'icon-world',                                   
            ),                                  
            __params__ = dict(
                has_children = False,
                uid = 'all',
                slot = 'internal',
                link = beans.Link(),
                
 
            )
        ),
           #:--- Downloading ---
                    dict(             
                        id = 'Downloading',                                                    
                        __params__ = dict(
                            link = beans.Link(),
                            has_children = False,
                            uid = 'downloading',
                            slot = 'internal',                            
                        ),
                        
                        ico = dict(
                            link = beans.Link(),
                            slot = 'internal', 
                            icon = 'icon-arrow_down',                                   
                        )
                    ),      
                    
                    #:--- Uploading ---
                    dict(             
                        id = 'Uploading',                                                    
                        __params__ = dict(
                            has_children = False,
                            uid = 'downloading',
                            slot = 'internal',
                            link = beans.Link(),
                        ),
                        
                        ico = dict(
                            link = beans.Link(),
                            slot = 'internal',                             
                            icon = 'icon-arrow_up',
                                   
                        )
                    ),                     
                                        
                    #:--- Queued ---
                    dict(             
                        id = 'Queued',                                                    
                        __params__ = dict(
                            has_children = False,
                            uid = 'queued',
                            slot = 'internal',
                            link = beans.Link(),
                        ),
                        ico = dict(
                            url = "/system/listing",
                            slot = 'internal', 
                            icon = 'icon-hourglass_go',
                                   
                        )       
                                                
                    ),                          
                                  
                    #:--- Completed ---
                    dict(             
                        id = 'Completed',                                                    
                        __params__ = dict(
                            has_children = False,
                            uid = 'completed',
                            slot = 'internal',
                            link = beans.Link(),
                        ),
                        ico = dict(
                            link = beans.Link(),
                            slot = 'internal', 
                            icon = 'icon-flag_green',
                                   
                        )                        
                    ),
                                    
                    
                    #:--- Founded ---
                    dict(             
                        id = 'Founded',                                                    
                        __params__ = dict(
                            has_children = False,
                            uid = 'queued',
                            slot = 'internal',
                            link = beans.Link(),
                        ),
                        ico = dict(
                            url = "/system/listing",
                            slot = 'internal', 
                            icon = 'icon-zoom',
                                   
                        )                                            
                    ),                          
    )    


@layout.route('/layout/@center')
@common.jsonify
def center():
    return beans.Slots(
         dict(
             id='mainlist',
             data=['CENTER'],
             margins=[5, 0, 5, 0],
             scroll='AUTO',
             split = True,
             link = beans.Link(
                url='/layout/dummy?fill=mainlist',
             ),                          
         ),
         
         dict(
             heading = 'Tools',
             id='tools',
             data=['SOUTH', 351],
             margins=[0, 0, 0, 0],
             collapsed = True,
             collapsible = True,             
             scroll='AUTO',
             split = True,
             layout = 'fit', 
             link = beans.Link(
                url='/layout/tools',
             ),     
         )               
                                
    )
    

@layout.route('/layout/tools')
@common.jsonify
def tools():        
    return beans.Tabs(
        heading = None,
        tabs = [
            beans.Tab(                    
                id = 'movies-ready',
                url = '/calendar/calendar-canvas',
                title = 'Calendar',
                params = dict(
                  icon = 'icon-calendar',    
                ),
            ),
            beans.Tab(                    
                id = 'movies-ready',
                url = '/layout/null',
                title = 'Files explorel',
                params = dict(
                  icon = 'icon-folder_explore',    
                ),
            ),
            beans.Tab(
                id = 'movies-downloading',
                url = '/layout/null',
                title = 'Tracker info',
                params = dict(
                  icon = 'icon-information',            
                ),                    
            ),
        ]        
    ) 
             

@layout.route('/layout/bottom')
@common.jsonify
def bottom():    
    ico_up = icon_factory('icon-arrow_up')
    speed_up = 'x.x'
    limit_up = 'x.x'
    total_up = 'x.x'
        
    ico_down = icon_factory('icon-arrow_down')
    speed_down = 'x.x'
    limit_down = 'x.x'
    total_down = 'x.x'
    
    rtorrent_ver = 'x.x'
    tab = '&nbsp;' * 6 
     
    return beans.HTML(
        content = """ 
            %(ico_up)s <b>Speed:</b> %(speed_up)s %(tab)s 
             <b>Limit:</b> %(limit_up)s %(tab)s
             <b>Total:</b> %(total_up)s %(tab)s
             
            %(ico_down)s <b>Speed:</b> %(speed_down)s %(tab)s 
             <b>Limit:</b> %(limit_down)s %(tab)s
             <b>Total:</b> %(total_down)s %(tab)s
             
             %(tab)s%(tab)s%(tab)s <b>rTorrent</b> %(rtorrent_ver)s                     
        """ % locals()          
    )


@layout.route('/layout/init')
@common.jsonify
def init():        
    return beans.TimerRegister(
        name = 'messages',
        action = '/layout/null',
        interval =  app.config['UPDATE_INTERVAL'],
        slot = 'internal',                        
    )
    
    
@layout.route('/layout/not-implemented', methods = ['GET', 'POST'])
@common.jsonify
def not_implemented():        
    return beans.Dialog(
        title = 'Informacja',
        text = 'Funkcja nie jest jeszcze zrobiona',
        
        buttons = [
            beans.Button(
                label = 'Ok',
                link = beans.Link(
                    url = '/layout/null',
                    slot = 'internal',
                )
            )                   
        ]                      
    )

@layout.route('/layout/dummy')
@common.jsonify
def dummy():
    return beans.HTML(
        content = (request.args['fill'] + ' ') * 8000                      
    )
    
    
@layout.route('/layout/null', methods = ['POST', 'GET'])
@common.jsonify
def null():        
    return beans.Null()