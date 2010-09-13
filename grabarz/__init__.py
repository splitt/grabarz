## -*- coding: utf-8 -*-
from __future__ import with_statement
from multiprocessing import Process, Pool
from datetime import datetime, timedelta
import os
import time
import sqlite3
import urllib
import threading 
from datetime import datetime, timedelta
from flask import Flask, g, session, request, redirect, make_response, session
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

import grabarz
path = '/'.join(grabarz.__path__[0].split('/')[:-1]) + '/__instance__.txt'
#: Read config depended on instance type
with open(path) as f:
    instance = f.read().capitalize().strip()
app.config.from_object('grabarz.config.%sConfig' % instance)


#: Creating directory structure for movies and tv shows
for attr in [d for d in app.config if 'DIR' in d]:
    try:
        os.makedirs(app.config[attr])
    except OSError:
        continue #: Path exists
    
    
#: Creating Task class and spawning cron process
class Task(db.Model):
    query = db.session.query_property()
    
    __tablename__ = 'tasks'
    __busy__ = False
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    execute_time = db.Column(db.DateTime)
    timedelta = db.Column(db.Interval)    
    run_periodic = db.Column(db.Boolean)    
            
    def __init__(self, url, delay, run_periodic = False):
        if not delay or delay == 'now':
            delay =  timedelta(seconds = 0)
            
        self.url = url
        self.timedelta = delay 
        self.run_periodic = run_periodic
        self.execute_time = datetime.now() + delay

    def schedule(self):
        self.execute_time = datetime.now() + self.timedelta
        self.__busy__ = False
        
    def execute(self):
        self.__busy__ = True
        urllib.urlopen(app.config['URL_ROOT'] + self.url)
        
        if self.run_periodic:
            self.schedule()
        else:
            db.session.delete(self)
        
    def cronify(self):
        db.session.add(self)
            
    def __repr__(self):
        return "<Task %s>" % self.execute_time
            
    
db.drop_all()
db.create_all()

#: Starting Cron process
def cron():
    time.sleep(1)
    while True:
        db.session.expire_all()
        for task in Task.query.all():            
            if task.execute_time < datetime.now() and not task.__busy__:
                
                p = Process(target = task.execute)
                p.start()                
                p.join()
        time.sleep(0.5)
                                                                        
p = Process(target = cron)
p.start()

from views.layout import layout
from views.movies import movies
app.register_module(layout)
app.register_module(movies)