## -*- coding: utf-8 -*-
import urllib
from datetime import timedelta, datetime

from grabarz import db, app


class ExtraModelFeatures(object):
    def commit(self):
        db.session.expire_all()
        db.session.add(self)
        db.session.commit()
        
    def push(self):
        db.session.add(self)

class Task(db.Model, ExtraModelFeatures):
    """ Task executed by cron """
    query = db.session.query_property()
    
    __tablename__ = 'tasks'
    __busy__ = False
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    execute_time = db.Column(db.DateTime)
    timedelta = db.Column(db.Interval)    
    run_periodic = db.Column(db.Boolean)    
            
    def __init__(self, url, delay = None, run_periodic = False):
        if not delay:
            delay = timedelta(seconds = 0)
            
        self.url = url
        self.timedelta = delay 
        self.run_periodic = run_periodic
        self.execute_time = datetime.now() + delay

    def schedule(self):
        self.execute_time = datetime.now() + self.timedelta
        
    def execute(self):
        app.logger.debug('!!!!executing task %s' % self.url)        
        if self.run_periodic:
            self.schedule()
        else:            
            db.session.delete(self)                           
            app.logger.debug('deleting task %s' % self.url)
            
        db.session.commit() 
            
        urllib.urlopen(app.config['URL_ROOT'] + self.url+'&task=1')
                
    def __repr__(self):
        return "<Task %s>" % self.execute_time
    
class CallbackUpdate(db.Model, ExtraModelFeatures):
    __tablename__ = 'callback_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    bean = db.Column(db.PickleType)
    exe_time = db.Column(db.DateTime)
        
    def __init__(self, bean, delay = None):
        if delay is None:
            delay = timedelta(seconds = 0)
        self.bean = bean
        self.exe_time = datetime.now() + delay        

             
    @staticmethod       
    def dump():
        db.session.flush()
        query = CallbackUpdate.query \
                              .filter(CallbackUpdate.exe_time <= datetime.now())
                                      
        rv =  [o.bean for o in query]
        query.delete()
        return rv