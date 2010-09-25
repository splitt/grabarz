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
    return len(os.listdir(path))



@layout.route('/layout/config')
@common.jsonify
def config():
    session['callback_updates'] = []
    session['filters'] = ['movies', 'tvshows']
    
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
        beans.Slot(
            id='top',
            data=['NORTH', 30],
            margins=[5, 5, 0, 5],
            scroll='NONE',            
            link = beans.Link(
                url="/layout/top",
            )
        ),          
        
        beans.Slot(
            id='left',
            heading = "Files",
            collapsible = True,
            data=['WEST', 140],
            margins=[5, 0, 0, 5],
            scroll='NONE',
            link = beans.Link(
                url="/layout/left",
            )
        ),
        
        beans.Slot(
            id='@center',
            split=True,
            data=['CENTER', 220],
            margins=[0, 5, 0, 5],
            scroll='NONE',
            link = beans.Link(
                url="/layout/@center",
            )
        ),
        
        beans.Slot(
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
            
            beans.MenuSeparator(),
            
            beans.MenuButton(
                icon = 'icon-film_link',
                title = 'TvShows scheduler',
                link = beans.Link(),
            ),                                                            
        ]                      
    )


@layout.route('/layout/left')
@common.jsonify
def left():
    return beans.Slots(
        beans.Slot(
            id = 'left-menu',
            data = ['NORTH', 136],
            link = beans.Link(
                url = '/layout/left-menu',
            )       
        ),
        beans.Slot(
            heading = 'Filter',
            id = 'left-filter',
            data = ['CENTER'],
            link = beans.Link(
                url = '/layout/left-filter',
            )                          
        ),                           
    )
    

@layout.route('/layout/left-menu')
@common.jsonify    
def left_menu():
    return beans.Tree(
        heading = None,
        sid = "menu",
        url = "/layout/left-tree-data",        
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
    )


@layout.route('/layout/left-filter')
@common.jsonify    
def left_filter():
    def get_icon(key):
        return 'accept' if key in session['filters'] else 'delete'
    
    url = '/layout/switch-filter?type=%s&current=%s'
            
    return beans.Listing(
        autoexpand_column = 'ico',
        sid = 'filters',
        paging = False,
        size = -1,
        
        columns = [
            beans.Column(
                id = 'name',
                title = '',
                width = '100',
            ),
            beans.Column(
                id = 'ico',
                title = '',
                width = '31',
                renderer = 'icon',
            ),                
        ],
        
        data = [
            beans.Row(
                name = 'movies',
                ico = dict(
                    icon = 'icon-%s' % get_icon('movies'),
                    url = url % ( 'movies', get_icon('movies')),
                ),                    
                __params__ =  dict(
                    uid = 'movies_filter',
                    url = url % ( 'movies', get_icon('movies')),                                                               
                ),                                
            ),
            beans.Row(
                name = 'tvshows',
                ico = dict(
                    icon = 'icon-%s' % get_icon('tvshows'),
                    url = url % ( 'tvshows', get_icon('tvshows')),
                ),                 
                __params__ =  dict(
                    uid = 'tvshows_filter',
                    url = url % ( 'tvshows', get_icon('tvshows')),                                    
                ),                                  
            ),                    
        ]             
    )
    

    
@layout.route('/layout/switch-filter', methods=['GET', 'POST'])
@common.jsonify
def switch_filter():
    type = request.args['type']
    current = request.args['current']
    
    if current == 'accept':
        session['filters'].remove(type)
    else:
        session['filters'].append(type)
        
    common.reload_slot(['left-filter', '@center'])
    
    return beans.Null()
    
@layout.route('/layout/left-tree-data', methods=['GET', 'POST'])
@common.jsonify
def left_data():
    gfc = get_folder_count
    
    folder_count = dict(
        downloading = gfc(app.config['MOVIES_DL_DIR']),
        uploading = gfc(app.config['MOVIES_UP_DIR']),     
        completed = gfc(app.config['MOVIES_COMPLETED_DIR']),
        queued = gfc(app.config['MOVIES_QUEUED_DIR']),
        founded = gfc(app.config['MOVIES_FOUNDED_DIR']),                        
    )
    folder_count['all'] = sum(folder_count.values()) 
    
    
    return beans.Data(
                      
        #:--- All files ---
        dict(             
            id = '--All files-- [%d]' % folder_count['all'],            
            ico = dict(
                url = "/system/listing",
                slot = 'internal', 
                icon = 'icon-world',                                   
            ),                                  
            __params__ = dict(
                has_children = False,
                uid = 'all',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=all',
                    slot = 'files-list',                   
                ),
                
 
            )
        ),
       #:--- Downloading ---
        dict(             
            id = 'Downloading [%d] ' % folder_count['downloading'],                                                    
            __params__ = dict(
                has_children = False,
                uid = 'downloading',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=dl',
                    slot = 'files-list',                   
                ),
            ),
            
            ico = dict(
                link = beans.Link(),
                slot = 'internal', 
                icon = 'icon-arrow_down',                                   
            )
        ),      
        
        #:--- Uploading ---
        dict(             
            id = 'Uploading [%d] ' % folder_count['uploading'],                                                    
            __params__ = dict(
                has_children = False,
                uid = 'uploading',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=up',
                    slot = 'files-list',                   
                ),
            ),
            
            ico = dict(
                link = beans.Link(),
                slot = 'internal',                             
                icon = 'icon-arrow_up',
                       
            )
        ),                     
                            
        #:--- Queued ---
        dict(             
            id = 'Queued [%d] ' % folder_count['queued'],                                                
            __params__ = dict(
                has_children = False,
                uid = 'queued',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=queued',
                    slot = 'files-list',                   
                ),
            ),
            ico = dict(
                url = "/system/listing",
                slot = 'internal', 
                icon = 'icon-hourglass_go',                       
            )       
                                    
        ),                          
                      
        #:--- Completed ---
        dict(             
            id = 'Completed [%d]' % folder_count['completed'],                                                    
            __params__ = dict(
                has_children = False,
                uid = 'completed',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=completed',
                    slot = 'files-list',                   
                ),                
            ),
            ico = dict(
                link = beans.Link(),
                slot = 'internal', 
                icon = 'icon-flag_green',
                       
            )                        
        ),
        
        #:--- Founded ---
        dict(             
            id = 'Founded [%d]' % folder_count['founded'],                                                 
            __params__ = dict(
                has_children = False,
                uid = 'founded',
                slot = 'internal',
                link = beans.Link(
                    url = '/files/files_listing?filter=all&type=founded',
                    slot = 'files-list',                   
                ),
            ),
            ico = dict(
                url = "/system/listing",
                slot = 'internal', 
                icon = 'icon-find',
            )                                            
        ),                          
    )


@layout.route('/layout/@center')
@common.jsonify
def center():
    return beans.Slots(
         dict(
             id='files-list',
             data=['CENTER'],
             margins=[5, 0, 5, 0],
             scroll='AUTO',
             split = True,
             link = beans.Link(
                url='/files/files_listing?filter=all&type=all',
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
                id = 'calendar-canvas',
                url = '/calendar/calendar-canvas',
                title = 'Calendar',
                params = dict(
                  icon = 'icon-calendar',    
                ),
            ),
            beans.Tab(                    
                id = 'folder-explore',
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