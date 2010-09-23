## -*- coding: utf-8 -*-
import time
import os
from os.path import join
import urllib
from multiprocessing import Process
from datetime import datetime, timedelta
        
from flask import Module, request
from flaskext.sqlalchemy import _create_scoped_session
from grabarz import app, db, common, models, views
from grabarz.lib import beans, torrent, utils

system = Module(__name__)
cron_db = _create_scoped_session(db)

PROTECTING_TIME = timedelta(seconds = 30)
 
                                                                     
def start_cron():    
    p = Process(target = lambda: urllib.urlopen(app.config['URL_ROOT'] + 
                                                '/system/cron-process'))
    p.start()

        
@system.route('/system/cron-process')
def cron():
    models.Task.delete()
    
    if app.config['FAKE_TORRENT']:
        models.Task(url = '/system/fake-torrent-process') 
    db.session.commit()
            
    app.logger.debug('cron started')
    
    protected = dict()    
    
    def is_procected(url):
        """ Procecting from execute the same task twice """
        if protected.get(url):
            if datetime.now() < protected[url]:
                return True
            else:
                del protected[url]                
        return False  
                
    while True:             
        for task in cron_db.query(models.Task).all():                   
            now = datetime.now()
            if task.execute_time < now and not is_procected(task.url):
                protected[task.url] = now + PROTECTING_TIME              
                p = Process(target = task.execute)
                p.start()
            time.sleep(0.5)
                
        time.sleep(0.5)



#@system.route('/system/add_fake_torrent')    
#def add_fake_torrent():
#    """ Process emulates rtorrent behaviur which allows easly debugging all 
#    system"""
#    
##    #: Make contener directory for files
##    full_work_dir = join(app.config['MOVIES_DOWNLOADING_DIR'], title)
##    
##    try:    
##        os.makedirs(full_work_dir)
##    except OSError:
##        pass #: Path propably exists     
    
    

@system.route('/system/window-torrent-add')
@common.jsonify
def window_torrent_add():    
    return beans.Window(                
        slotname = 'window-torrent-add',
        heading = 'Dodaj plik torrent',
        height = 130,             
        object= beans.Form(
            slotname = '/movies/add',            
            buttons = [
                beans.Button(
                     slot = "content",
                     link = beans.Link(
                        url = "/system/fetch-torrent-file",
                        slot = "window_add_entry",
                     ),
                     label = "Dodaj"
                ),
            ],    
            formdefs = [
                beans.CharField(
                    name='torrent_url',
                    label='Podaj adres pliku torrent',
                    width=350,
                 ),                      
            ],
        ),
    )
    
    
@system.route('/system/fetch-torrent-file', methods=['GET', 'POST'])
@common.jsonify
def fetch_torrent_file():
    """ Reads information from torrent file and creates grabarz.ini 
    file for given movie."""
                          
    if views.files.feed_movie() == 'ERROR':
        return beans.Dialog(
            title = 'Nie rozpoznano filmu ani serialu',
            text = 'Czy chcesz zacząć pobierąć torrent pomimo faktu, że system'\
            'nie rozpoznał pliku?'                    
        )            
    return beans.Infobox(
        text = 'Rozpoczęto pobieranie nowego filmu'
    )





    
#@system.route('/make_slot')
#@common.jsonify
#def make_slot():
#    url = request.args['url']    
#    return beans.Slots(
#        dict(
#            layout = 'fit',                
#            scroll = 'AUTOY',
#            id = 'slotted-%s' % url,
#            url = url,
#            margins = [0,0,40,0],
#            data = ['CENTER'],
#        ),
#    )

