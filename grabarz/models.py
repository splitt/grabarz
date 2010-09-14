## -*- coding: utf-8 -*-
import urllib
from datetime import timedelta, datetime

from grabarz import db, app

class Task(db.Model):
    """ Task executed by cron """
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
            
        db.session.commit()
        
    def cronify(self):
        app.logger.debug('adding task %s do cron' % self.url)
        db.session.add(self)
        db.session.commit()
            
    def __repr__(self):
        return "<Task %s>" % self.execute_time
    
#class Messages(db.Model):
#    __tablename__ = 'system'
#    
#    def __init__(self, updates):            
#        self.updates = updates
#        
#    def update(self):
#        pass
#    
#    def get(self):
#        pass