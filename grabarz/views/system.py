## -*- coding: utf-8 -*-
import time
import urllib
from multiprocessing import Process
from datetime import datetime, timedelta

        
from flask import Module, request
from flaskext.sqlalchemy import _create_scoped_session
from grabarz import app, db, common, models
from grabarz.lib import beans, utils

system = Module(__name__)

cron_db = _create_scoped_session(db)
PROTECTING_TIME = timedelta(seconds = 30)
                                                                     
def start_cron():
    app.logger.debug('starting cron')
    p = Process(target = lambda: urllib.urlopen('/system/cron'))
    p.start()

        
@system.route('/system/cron')
def cron():    
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
            time.sleep(3)
                
        time.sleep(0.5)


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
                        url = "/movies/fetch-torrent-file",
                        slot = "window_add_entry",
                     ),
                     label = "Dodaj"
                ),
            ],    
            formdefs = [
                beans.CharField(
                    name='torrent_src',
                    label='Podaj adres pliku torrent',
                    width=350,
                 ),                      
            ],
        ),
    )
    
@system.route('/make_slot')
@common.jsonify
def make_slot():
    url = request.args['url']    
    return beans.Slots(
        dict(
            layout = 'fit',                
            scroll = 'AUTOY',
            id = 'slotted-%s' % url,
            url = url,
            margins = [0,0,40,0],
            data = ['CENTER'],
        ),
    )

